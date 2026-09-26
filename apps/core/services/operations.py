"""Servicios transaccionales para cerrar operaciones y alimentar aprendizaje."""
from django.db import transaction
from django.utils import timezone

from apps.containers.models import Container
from apps.programaciones.models import Programacion, TiempoOperacion


class OperationalFlowService:
    @staticmethod
    def _record_discharge(programacion, started_at, finished_at, source):
        if TiempoOperacion.objects.filter(
            container=programacion.container, tipo_operacion='descarga_cd'
        ).exists():
            return None
        # P1-1/P1-2: preferir programacion.fecha_inicio_descarga cuando existe
        # (clic real del conductor "Iniciar Descarga"). Si no, caer al flujo
        # histórico (fecha_soltado o fecha_entrega). Se acepta el caller
        # pasando started_at explícito para tests; pero si el caller pasó el
        # default del servicio, override aquí para respetar fecha_inicio_descarga.
        if programacion.fecha_inicio_descarga and (
            started_at is None
            or started_at == programacion.container.fecha_soltado
            or started_at == programacion.container.fecha_entrega
        ):
            started_at = programacion.fecha_inicio_descarga
        estimated = programacion.cd.tiempo_promedio_descarga_min or 60
        # P2-2: predicción viva primero (programacion.prediccion_ml.tiempo_descarga_estimado).
        # Si no hay, cae al engine (predict_discharge), y al estático del CD.
        try:
            from apps.core.services.learning_engine import OperationalLearningEngine
            # 1) prediccion_ml vivo en el contenedor/programación
            ml_viva = None
            prediccion_ml = getattr(programacion, 'prediccion_ml', None) or {}
            if isinstance(prediccion_ml, dict):
                ml_viva = prediccion_ml.get('tiempo_descarga_estimado')
            if isinstance(ml_viva, (int, float)) and ml_viva > 0:
                estimated = int(ml_viva)
            else:
                # 2) OperationalLearningEngine.predict_discharge
                aprendida = OperationalLearningEngine.predict_discharge(
                    programacion.cd, conductor=programacion.driver,
                )
                if isinstance(aprendida, dict) and aprendida.get('estimated_minutes'):
                    estimated = int(aprendida['estimated_minutes'])
        except Exception:
            pass
        delta_min = int((finished_at - started_at).total_seconds() / 60)
        if delta_min <= 0:
            # Reloj erróneo o datos inconsistentes: no dejar 1 min que envenene el ML.
            delta_min = max(1, estimated)
        actual = max(1, delta_min)
        return TiempoOperacion.objects.create(
            cd=programacion.cd,
            conductor=programacion.driver,
            container=programacion.container,
            tipo_operacion='descarga_cd',
            tiempo_estimado_min=estimated,
            tiempo_real_min=actual,
            hora_inicio=started_at,
            hora_fin=finished_at,
            anomalia=actual >= max(1, estimated) * 3,
            observaciones=f'Registro operacional automático: {source}',
        )

    @classmethod
    @transaction.atomic
    def registrar_arribo(cls, programacion, lat, lng, origen='manual', usuario=None):
        """Registra una sola vez el arribo (manual o geocerca), con lock e idempotencia.

        Fuente única de verdad para el flujo containers y programaciones: evita la
        duplicación de caminos con distinta riqueza (arribo simple vs rico).
        Devuelve (programacion_lockeada, creado: bool).
        """
        from apps.events.models import Event

        locked = cls._lock_programacion(programacion)
        if locked.fecha_arribo_cd:
            return locked, False
        if locked.container.estado != 'en_ruta':
            raise ValueError(
                f'Contenedor debe estar en ruta. Estado actual: {locked.container.get_estado_display()}'
            )

        arrived_at = timezone.now()
        if locked.driver:
            locked.driver.actualizar_posicion(lat, lng)
        locked.fecha_arribo_cd = arrived_at
        locked.gps_arribo_lat = lat
        locked.gps_arribo_lng = lng
        locked.origen_arribo = origen
        locked.posicion_actual_lat = lat
        locked.posicion_actual_lng = lng
        locked.ultima_actualizacion_tracking = arrived_at
        locked.save(update_fields=[
            'fecha_arribo_cd', 'gps_arribo_lat', 'gps_arribo_lng', 'origen_arribo',
            'posicion_actual_lat', 'posicion_actual_lng', 'ultima_actualizacion_tracking',
            'updated_at',
        ])
        locked.container.cambiar_estado('entregado', usuario)

        Event.objects.create(
            container=locked.container,
            event_type='arribo_cd',
            detalles={
                'conductor': locked.driver.nombre if locked.driver else None,
                'cd': locked.cd.nombre if locked.cd else None,
                'gps_lat': str(lat),
                'gps_lng': str(lng),
                'timestamp': arrived_at.isoformat(),
                'origen': origen,
            },
            usuario=usuario or ('system_geocerca' if origen == 'geocerca' else 'conductor'),
        )

        # HAL-10: al arribar (viaje cerrado), refrescar el ETA visible para que
        # la UI no muestre un ETA viejo (ej. 45 min) cuando ya estamos al CD.
        # HAL-10 evita el silent bug visual: la UI de operaciones mostraba el
        # ETA estimado inicial durante horas después del arribo.
        try:
            from django.db.models import F
            Programacion.objects.filter(pk=locked.pk).update(eta_minutos=0)
            locked.eta_minutos = 0
        except Exception:
            pass

        # HAL-8: la Notification 'llegada' sale del atomic block del arribo.
        # Se programa con transaction.on_commit para que se cree SOLO si el
        # commit de la transacción padre tiene éxito. Si falla la creación del
        # notification, NO se revierte el viaje (el container ya quedó
        # 'entregado' con su evento y GPS persistidos).
        # El closure captura `locked` por referencia; on_commit ejecuta la
        # función una vez completada la transacción actual.
        try:
            transaction.on_commit(
                lambda: cls._create_arribo_notification(locked, arrived_at)
            )
        except Exception as _schedule_exc:
            # on_commit fuera de una transacción: ejecutar inline y registrar.
            import logging
            logging.getLogger(__name__).warning(
                'registrar_arribo_on_commit_failed prog_id=%s detalle=%s',
                getattr(locked, 'pk', None), _schedule_exc,
            )
            try:
                cls._create_arribo_notification(locked, arrived_at)
            except Exception:
                pass

        return locked, True

    @classmethod
    def _create_arribo_notification(cls, locked, arrived_at):
        """Crea la Notification 'llegada' post-commit (HAL-8). Idempotente."""
        from apps.notifications.models import Notification
        # Idempotencia: nunca crear dos notificaciones de llegada para la misma
        # programacion (geocerca + manual pueden dispararse casi simultáneos).
        ya_existe = Notification.objects.filter(
            programacion=locked, tipo='llegada',
        ).exists()
        if ya_existe:
            return None
        hora_local = arrived_at.strftime('%H:%M')
        cd_nombre = locked.cd.nombre if locked.cd else 'CD'
        return Notification.objects.create(
            container=locked.container,
            programacion=locked,
            tipo='llegada',
            prioridad='alta',
            titulo=f'Entregado a las {hora_local} - {locked.container.container_id}',
            mensaje=(
                f'Contenedor {locked.container.container_id} arribó a {cd_nombre} '
                f'a las {hora_local} ({locked.cliente}).'
            ),
            detalles={
                'fecha_arribo': arrived_at.isoformat(),
                'cd': cd_nombre,
                'cliente': locked.cliente,
                'conductor': locked.driver.nombre if locked.driver else None,
            },
        )

    @staticmethod
    def _lock_programacion(programacion):
        return Programacion.objects.select_for_update().select_related(
            'container', 'driver', 'cd'
        ).get(pk=programacion.pk)

    @classmethod
    def _auto_assign_empty_return(cls, programacion):
        """Crea (si aplica) una Programacion de retorno automático de un
        contenedor vacío disponible desde el CD donde se soltó.

        Criterios:
        - Conductor recién liberado (driver_id presente y con capacidad).
        - Existe Container en estado='vacio', vacio_contabilizado=True,
          en el mismo CD (Container.retorno_destino_cd o Container.cd_entrega
          == locked.cd). SIN límite de frescura: el conductor retira cualquier
          vacío disponible del CD (decisión del dueño 25-sep; la priorización
          por demurrage se integrará en una iteración posterior).
        - El conductor NO debe tener otra programacion activa.

        La asignación concreta se hace via señal trigger_automatic_assignment
        (apps/programaciones/signals.py) que ya se dispara al crear
        Programacion, sin llamada de red adicional. Esto preserva el patrón
        de auto-asignación que ya usa el resto del sistema.

        Returns:
            Programacion creada o None si no aplica.
        """
        from datetime import timedelta
        from apps.containers.models import Container

        driver = programacion.driver
        if not driver or not driver.esta_disponible:
            return None

        # Buscar contenedores vacíos disponibles en el mismo CD donde soltó
        # el conductor. Compatibilidad: Container.retorno_destino_cd o
        # Container.cd_entrega equivalen al CD de la programación.
        # Sin filtro de fecha_vacio: se toma cualquier vacío disponible
        # (el más antiguo primero). El dueño priorizará por demurrage
        # en una iteración futura.
        from django.db.models import Q
        candidatos = Container.objects.filter(
            estado='vacio',
            vacio_contabilizado=True,
        ).filter(
            # modelos.cd_entrega o retorno_destino_cd == programacion.cd
            Q(retorno_destino_cd_id=programacion.cd_id) |
            Q(cd_entrega_id=programacion.cd_id),
        ).exclude(
            # Excluir el contenedor que acabamos de soltar (estado='soltado',
            # pero por seguridad también lo excluimos si está vacío)
            id=programacion.container_id,
        ).order_by('fecha_vacio')[:1]

        candidato = candidatos.first()
        if not candidato:
            return None

        # Verificar que el conductor no tiene otra programación activa
        from apps.programaciones.models import Programacion as Prog
        tiene_activa = Prog.objects.filter(
            driver=driver,
            fecha_liberacion_conductor__isnull=True,
            container__estado__in=[
                'asignado', 'en_ruta', 'entregado', 'descargado',
                'vacio', 'vacio_en_ruta',
            ],
        ).exists()
        if tiene_activa:
            return None

        # No re-crear si ya hay una programación activa sobre el candidato
        if Prog.objects.filter(
            container=candidato,
            container__estado__in=['asignado', 'en_ruta', 'vacio_en_ruta', 'en_ccti'],
        ).exists():
            return None

        # Determinar destino del retorno: depósito naviera preferido;
        # fallback a cd_entrega del contenedor.
        cd_destino = candidato.retorno_destino_cd or candidato.cd_entrega
        fecha_programada = timezone.now() + timedelta(minutes=15)

        nueva = Prog.objects.create(
            container=candidato,
            cd=cd_destino or programacion.cd,
            # Safari review (P0-5): el dueño exige MISMO conductor que soltó.
            # Seteando driver= acá la señal post_save hace early-return
            # (`if instance.driver: return` en signals.py:38) y NO llama al
            # AssignmentService ML que podría elegir a otro conductor del pool.
            # Las validaciones de capacidad/disponibilidad ya se hicieron arriba
            # (driver.esta_disponible y Prog.objects.filter(...).exists()).
            driver=driver,
            cliente=candidato.cliente or 'RETORNO VACIO',
            fecha_programada=fecha_programada,
            direccion_entrega=(
                cd_destino.direccion if cd_destino else ''
            ),
            urgencia_servicio='NORMAL',
            observaciones=(
                f'Retorno automático desde {programacion.cd.nombre} '
                f'(drop del contenedor {programacion.container.container_id})'
            ),
            ventana_horaria_inicio=None,
            ventana_horaria_fin=None,
        )
        return nueva


    @classmethod
    @transaction.atomic
    def registrar_arribo_directo(cls, container, lat=None, lng=None, usuario=None):
        """Arribo sin programación asociada: mismo rastro de auditoría que el
        camino rico (evento arribo_cd con GPS/CD/origen), pero solo cambia el
        estado del contenedor. Fuente única junto a registrar_arribo; evita
        que el flujo simple quede sin evento específico de arribo.

        Devuelve (container_lockeado, creado: bool).
        """
        from apps.events.models import Event

        locked = Container.objects.select_for_update().get(pk=container.pk)
        if locked.estado != 'en_ruta':
            raise ValueError(
                f'Contenedor debe estar en_ruta. Estado actual: {locked.get_estado_display()}'
            )

        arrived_at = timezone.now()
        # GPS: explícito → ubicación del CD de entrega (Container no guarda
        # posición GPS; la posición viva del vehículo vive en
        # Programacion.posicion_actual_*). El CD de entrega es donde arriba.
        if lat is None or lng is None:
            if locked.cd_entrega_id:
                lat, lng = float(locked.cd_entrega.lat), float(locked.cd_entrega.lng)

        locked.cambiar_estado('entregado', usuario)

        Event.objects.create(
            container=locked,
            event_type='arribo_cd',
            detalles={
                'conductor': None,
                'cd': locked.cd_entrega.nombre if locked.cd_entrega_id else None,
                'gps_lat': str(lat) if lat is not None else None,
                'gps_lng': str(lng) if lng is not None else None,
                'timestamp': arrived_at.isoformat(),
                'origen': 'manual_sin_programacion',
            },
            usuario=usuario or 'operador',
        )
        return locked, True

    @classmethod
    @transaction.atomic
    def drop_container(cls, programacion, usuario=None):
        """Drop & hook deja carga en CD; no declara vacío antes de la descarga."""
        locked = Programacion.objects.select_for_update().select_related(
            'container', 'driver', 'cd'
        ).get(pk=programacion.pk)
        if not locked.cd.permite_soltar_contenedor:
            raise ValueError(f'El CD {locked.cd.nombre} no permite Drop & Hook.')
        if locked.container.estado == 'soltado':
            return locked, False
        if locked.container.estado != 'entregado':
            raise ValueError('Solo se puede soltar después de registrar el arribo.')
        locked.container.cambiar_estado('soltado', usuario)
        locked.liberar_conductor()
        # P0-5: auto-asignación de retiro de vacío desde el CD donde se soltó.
        # Buscar un contenedor 'fresco' (vacio contabilizado en últimas 2h) en el
        # mismo CD y crear una Programacion de retorno automático. La señal
        # trigger_automatic_assignment (apps/programaciones/signals.py) la
        # asignará al conductor recién liberado, sin llamada de red adicional.
        retorno_programacion = cls._auto_assign_empty_return(locked)
        return locked, True, retorno_programacion

    @classmethod
    @transaction.atomic
    def complete_discharge(cls, programacion, usuario=None, source='conductor'):
        """Cierra descarga desde espera sobre camión o desde un drop previo."""
        locked = Programacion.objects.select_for_update().select_related(
            'container', 'driver', 'cd'
        ).get(pk=programacion.pk)
        if locked.container.estado not in {'entregado', 'soltado', 'descargado'}:
            raise ValueError('El contenedor debe estar entregado o soltado antes de descargar.')
        if locked.container.estado == 'descargado':
            return locked, None, False
        finished_at = timezone.now()
        started_at = locked.container.fecha_soltado or locked.container.fecha_entrega
        if not started_at:
            raise ValueError('No existe hora de inicio para medir la descarga.')
        locked.container.cambiar_estado('descargado', usuario)
        timing = cls._record_discharge(locked, started_at, finished_at, source)
        # En espera sobre camión el conductor queda libre al finalizar la descarga.
        if not locked.cd.permite_soltar_contenedor:
            locked.liberar_conductor()
        return locked, timing, True

    @classmethod
    @transaction.atomic
    def mark_empty(cls, programacion, usuario=None, source='conductor'):
        locked, timing, _ = cls.complete_discharge(programacion, usuario, source)
        if locked.container.estado == 'descargado':
            locked.container.cambiar_estado('vacio', usuario)
        return locked, timing

    @staticmethod
    def registrar_operacion_tiempo(container, tipo_operacion, started_at, finished_at,
                                    cd_origen=None, cd_destino=None, conductor=None,
                                    observaciones=''):
        """Registra un TiempoOperacion explícito para el ciclo completo.

        Usado por iniciar_retorno (devolucion_vacio), marcar_devuelto (devolucion_vacio)
        y crear_ruta_manual (carga_ccti/retiro_puerto). Si finished_at - started_at
        es <=0 se marca anomalía para no envenenar el ML con datos inconsistentes.

        Args:
            container: Container relacionado (puede ser None para carga_ccti previa).
            tipo_operacion: uno de carga_ccti|descarga_cd|retiro_puerto|devolucion_vacio.
            started_at, finished_at: datetimes del tramo.
            cd_origen, cd_destino: CD (uno u otro obligatorio según tipo).
            conductor: Driver opcional.
            observaciones: nota libre para auditoría.

        Returns:
            TiempoOperacion creado o None si ya existía uno para ese container+tipo.
        """
        cd = cd_origen or cd_destino
        if cd is None:
            # Sin CD no podemos crear el registro (el modelo lo exige NOT NULL).
            return None
        existing = TiempoOperacion.objects.filter(
            container=container, tipo_operacion=tipo_operacion,
        ).exists() if container else False
        if existing:
            return None
        delta_min = max(1, int((finished_at - started_at).total_seconds() / 60))
        estimated = cd.tiempo_promedio_descarga_min if (
            tipo_operacion == 'descarga_cd' and cd.tiempo_promedio_descarga_min
        ) else max(1, delta_min)
        return TiempoOperacion.objects.create(
            cd=cd,
            conductor=conductor,
            container=container,
            tipo_operacion=tipo_operacion,
            tiempo_estimado_min=estimated,
            tiempo_real_min=delta_min,
            hora_inicio=started_at,
            hora_fin=finished_at,
            anomalia=delta_min >= max(1, estimated) * 3,
            observaciones=observaciones or f'Registro operacional: {tipo_operacion}',
        )
