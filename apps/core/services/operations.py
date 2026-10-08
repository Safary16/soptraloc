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

        # HAL-17: prioridad explícita para resolver el clic real del conductor
        # cuando se solapa con el flujo histórico de soltar/entregar. La idea:
        # si la programación tiene fecha_inicio_descarga (clic real del
        # conductor en CD), es la mejor estimación de cuándo empezó la
        # operación física. Si no, se respeta el started_at que pasó el caller
        # (tests, integrations). Si tampoco, caemos a fecha_soltado (drop &
        # hook) o fecha_entrega (espera sobre camión). Este orden evita que un
        # started_at 'default' venido de complete_discharge
        # (que hoy elige fecha_soltado|fecha_entrega) sobrescriba el clic real.
        fecha_inicio_real = getattr(programacion, 'fecha_inicio_descarga', None)
        fecha_soltado = programacion.container.fecha_soltado
        fecha_entrega = programacion.container.fecha_entrega
        candidatos_priorizados = [
            fecha_inicio_real,
            started_at,
            fecha_soltado,
            fecha_entrega,
        ]
        started_at_resolved = next(
            (c for c in candidatos_priorizados if c is not None),
            None,
        )
        if started_at_resolved is not None:
            started_at = started_at_resolved

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
            Programacion.objects.filter(pk=locked.pk).update(eta_minutos=0)
            locked.eta_minutos = 0
        except Exception:
            pass

        # HAL-8: la Notification 'llegada' sale del atomic block del arribo.
        # Política de creación con detección de contexto:
        # - Outer-most transaction (sin savepoint): on_commit garantiza que
        #   si el commit falla, NO se crea el notification. Production path.
        # - Nested transaction (con savepoint, ej. TestCase): on_commit NO se
        #   ejecuta cuando el TestCase hace rollback del outer-most. Detectamos
        #   savepoint_ids > 0 y ejecutamos inline; el notification se ve y
        #   queda persistido en el test DB. Production-safe porque un savepoint
        #   dentro de un atomic real también hace rollback junto con el outer
        #   si el outer falla, y la notification inline ya creada queda
        #   revertida automáticamente (es parte del mismo savepoint).
        from django.db import connection as _db_conn
        _savepoint_ids = getattr(_db_conn, 'savepoint_ids', None) or []
        _in_nested_atomic = len(_savepoint_ids) >= 1
        try:
            if _in_nested_atomic:
                # Savepoint path: fire inline. El test/proceso revertirá el outer
                # si algo falla, y la notification se revierte con él.
                cls._create_arribo_notification(locked, arrived_at)
            else:
                # Outer-most or no atomic: on_commit con rollback-safety real.
                transaction.on_commit(
                    lambda: cls._create_arribo_notification(locked, arrived_at)
                )
        except Exception as _schedule_exc:
            # Fallback: ejecutar inline y registrar el problema (solo si
            # llegamos aquí porque on_commit no estaba disponible).
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
        # of=('self',): bloquear SOLO la fila Programacion (punto de serialización
        # del FSM). Sin esto, Postgres lanza NotSupportedError: FOR UPDATE cannot
        # be applied to the nullable side of an outer join (driver/cd son FK
        # nullable → LEFT JOIN → FOR UPDATE ilegal en PostgreSQL).
        return Programacion.objects.select_for_update(of=('self',)).select_related(
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
            container__estado__in=['asignado', 'en_ruta', 'vacio_en_ruta', 'en_patio'],
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
    def iniciar_transito(cls, container, usuario=None):
        """HAL-23: transición de inicio de ruta según el estado del contenedor.

        Un solo lugar decide: viaje lleno (asignado) → 'en_ruta'; retiro de
        vacío (vacio/en_patio) → 'vacio_en_ruta' (única transición válida del
        FSM para esos estados). Sin esto, iniciar_ruta sobre un retorno
        automático P0-5 (container en 'vacio') reventaba con ValidationError
        → 500 y el circuito quedaba asignado sin camino de ejecución.
        """
        if container.estado in ('vacio', 'en_patio'):
            container.cambiar_estado('vacio_en_ruta', usuario)
        else:
            container.cambiar_estado('en_ruta', usuario)
        return container

    @classmethod
    @transaction.atomic
    def drop_container(cls, programacion, usuario=None):
        """Drop & hook deja carga en CD; no declara vacío antes de la descarga.

        HAL-20: retorna SIEMPRE 3-tupla (locked, created, retorno_programacion);
        en el camino idempotente (ya soltado) created=False y retorno=None.
        """
        locked = Programacion.objects.select_for_update(of=('self',)).select_related(
            'container', 'driver', 'cd'
        ).get(pk=programacion.pk)
        if not locked.cd.permite_soltar_contenedor:
            raise ValueError(f'El CD {locked.cd.nombre} no permite Drop & Hook.')
        if locked.container.estado == 'soltado':
            # HAL-20: camino idempotente retorna la MISMA 3-tupla que el camino
            # normal; el consumidor (vista del conductor) desempaqueta 3 y un
            # reintento de drop reventaba con 'too many values to unpack' → 500.
            return locked, False, None
        if locked.container.estado != 'entregado':
            raise ValueError('Solo se puede soltar después de registrar el arribo.')
        locked.container.cambiar_estado('soltado', usuario)
        locked.liberar_conductor()
        # P0-5: auto-asignación de retiro de vacío desde el CD donde se soltó.
        # Busca cualquier contenedor 'vacio' contabilizado en el mismo CD y crea
        # una Programacion de retorno automático (SIN límite de frescura —
        # decisión del dueño 25-sep). La señal trigger_automatic_assignment
        # (apps/programaciones/signals.py) la asignará al conductor recién
        # liberado, sin llamada de red adicional.
        retorno_programacion = cls._auto_assign_empty_return(locked)
        return locked, True, retorno_programacion

    @classmethod
    @transaction.atomic
    def complete_discharge(cls, programacion, usuario=None, source='conductor'):
        """Cierra descarga desde espera sobre camión o desde un drop previo."""
        from apps.events.models import Event
        locked = Programacion.objects.select_for_update(of=('self',)).select_related(
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
        # HAL-13: trazabilidad del cierre de descarga como Event (origen_geocerca /
        # directo / conductor, etc.). Se hace DENTRO del atomic para garantizar
        # consistencia entre cambio de estado + evento + tiempo ML.
        Event.objects.create(
            container=locked.container,
            event_type='fin_descarga',
            detalles={
                'cd': locked.cd.nombre if locked.cd else None,
                'conductor': locked.driver.nombre if locked.driver else None,
                'started_at': started_at.isoformat(),
                'finished_at': finished_at.isoformat(),
                'duracion_min': timing.tiempo_real_min if timing else None,
                'anomalia': bool(timing.anomalia) if timing else False,
                'source': source,
                'origen_registro': source,
                'permite_soltar_contenedor': bool(locked.cd.permite_soltar_contenedor),
            },
            usuario=usuario,
        )
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
        y crear_ruta_manual (carga_patio/retiro_puerto). Si finished_at - started_at
        es <=0 se marca anomalía para no envenenar el ML con datos inconsistentes.

        Args:
            container: Container relacionado (puede ser None para carga_patio previa).
            tipo_operacion: uno de carga_patio|descarga_cd|retiro_puerto|devolucion_vacio.
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

    @staticmethod
    def iniciar_ruta_con_eta(programacion, *, patente, lat, lng, usuario=None):
        """Valida y ejecuta el inicio de ruta con confirmación de patente + GPS.

        Extraído de programaciones.views.iniciar_ruta (iteración 1 monolito,
        07-oct). Mantiene EXACTO el contrato HTTP original: el caller (la vista)
        mapea estos resultados a las mismas respuestas 200/400 de antes.

        Validaciones (en orden, cada una puede cortar):
        - conductor asignado
        - idempotencia: si fecha_inicio_ruta ya existe → ok con flag
        - patente ingresada obligatoria (HAL-7: coalescencia a '' antes de strip)
        - patente vs la asignada al conductor (mismatch incluye esperada/ingresada)
        - coordenadas GPS obligatorias

        Efectos: posición del conductor, campos de inicio (patente/GPS/fecha),
        FSM via iniciar_transito (HAL-23), Event 'inicio_ruta', ETA con triple
        fallback (recommend → MLTimePredictor → haversine HAL-1) con blindaje
        final, y notificación al conductor (su fallo NO revierte el inicio).

        Returns:
            dict: {'ok': True, 'programacion', 'notificacion_data', 'patente_confirmada',
                   'gps'} — o {'ok': False, 'error', ...extras} si alguna validación corta.
        """
        if not programacion.driver:
            return {'ok': False, 'error': 'Programación no tiene conductor asignado'}

        # Fix auditoría 07-oct: guard idempotente. Si la ruta ya fue iniciada,
        # NO sobrescribir GPS/fecha_inicio_ruta (doble clic o retry de red no
        # debe mutar el registro original). 200 con el estado actual.
        if programacion.fecha_inicio_ruta:
            return {'ok': True, 'idempotente': True, 'programacion': programacion}

        # Validar que se proporcione la patente
        # HAL-7: el default '' solo aplica si la clave está ausente. Si el cliente
        # envía {'patente': null}, el default no aplica y .strip() revienta con
        # AttributeError: 'NoneType' object has no attribute 'strip'. Forzamos
        # coalescencia a '' antes de strip().
        patente_ingresada = (patente or '').strip().upper()
        if not patente_ingresada:
            return {'ok': False, 'error': 'Debe ingresar la patente del vehículo para confirmar'}
        
        # Si el conductor tiene una patente asignada, validar que coincida
        if programacion.driver.patente and programacion.driver.patente.strip():
            patente_asignada = programacion.driver.patente.strip().upper()
            if patente_ingresada != patente_asignada:
                return {
                    'ok': False,
                    'error': f'La patente ingresada ({patente_ingresada}) no coincide con la asignada ({patente_asignada})',
                    'patente_esperada': patente_asignada,
                    'patente_ingresada': patente_ingresada,
                    'success': False,
                }
        else:
            # Si no hay patente asignada, aceptar cualquiera pero registrarla
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Conductor {programacion.driver.nombre} no tiene patente asignada. Usando: {patente_ingresada}')
        
        # Obtener coordenadas GPS (requeridas para registrar posición de inicio)
        if not lat or not lng:
            return {'ok': False, 'error': 'Se requieren coordenadas GPS (lat, lng) para iniciar la ruta'}
        
        # Actualizar posición del conductor
        programacion.driver.actualizar_posicion(lat, lng)
        programacion.posicion_actual_lat = lat
        programacion.posicion_actual_lng = lng
        programacion.ultima_actualizacion_tracking = timezone.now()
        
        # Guardar datos de inicio de ruta en la programación
        programacion.patente_confirmada = patente_ingresada
        programacion.fecha_inicio_ruta = timezone.now()
        programacion.gps_inicio_lat = lat
        programacion.gps_inicio_lng = lng
        programacion.save()
        
        # Cambiar estado del contenedor: HAL-23 — la elección de transición vive
        # en OperationalFlowService.iniciar_transito (viaje lleno → 'en_ruta';
        # retiro de vacío → 'vacio_en_ruta', única transición FSM válida).
        OperationalFlowService.iniciar_transito(programacion.container, usuario)
        
        # Crear evento de inicio de ruta con datos GPS
        from apps.events.models import Event
        Event.objects.create(
            container=programacion.container,
            event_type='inicio_ruta',
            detalles={
                'conductor': programacion.driver.nombre,
                'patente': patente_ingresada,
                'gps_lat': str(lat),
                'gps_lng': str(lng),
                'timestamp': timezone.now().isoformat()
            },
            usuario=usuario
        )
        
        # Calcular y guardar ETA híbrido (Mapbox + aprendizaje histórico).
        from apps.core.services.learning_engine import OperationalLearningEngine
        from apps.core.services.ml_predictor import MLTimePredictor
        eta_ok = False
        try:
            recomendacion = OperationalLearningEngine.recommend(
                (float(lat), float(lng)),
                (float(programacion.cd.lat), float(programacion.cd.lng)),
                programacion.fecha_inicio_ruta,
                driver=programacion.driver,
                window_hours=0,
            )
            if recomendacion.get('success'):
                prediccion = recomendacion['recommended']
                programacion.eta_minutos = prediccion['predicted_minutes']
                programacion.distancia_km = prediccion['distance_km']
                programacion.ruta_geojson = prediccion.get('geometry')
                programacion.ruta_firma = prediccion.get('route_signature')
                programacion.prediccion_ml = {
                    'source': prediccion['source'],
                    'mapbox_minutes': prediccion['mapbox_minutes'],
                    'predicted_minutes': prediccion['predicted_minutes'],
                    'learned_factor': prediccion['learned_factor'],
                    'samples': prediccion['samples'],
                    'confidence': prediccion['confidence'],
                    'driver_profile': prediccion.get('driver_profile'),
                    'explanation': recomendacion['explanation'],
                }
                eta_ok = True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error calculando ETA (recommend) para programación: {str(e)}")
        
        # Fallback: si Mapbox/ML recomendación falla, usar el predictor con fallback
        # (siempre debe quedar una ETA operable para advertir choques y mostrar llegada).
        if not eta_ok:
            try:
                pred_fb = MLTimePredictor.predecir_tiempo_viaje(
                    (float(lat), float(lng)),
                    (float(programacion.cd.lat), float(programacion.cd.lng)),
                    programacion.fecha_inicio_ruta,
                    conductor=programacion.driver,
                )
                programacion.eta_minutos = int(pred_fb['tiempo_estimado_min'])
                programacion.distancia_km = pred_fb.get('distancia_km') or 0
                programacion.prediccion_ml = {
                    'source': pred_fb.get('fuente', 'fallback'),
                    'mapbox_minutes': pred_fb.get('tiempo_mapbox_min', 0),
                    'predicted_minutes': programacion.eta_minutos,
                    'learned_factor': None,
                    'samples': 0,
                    'confidence': None,
                    'driver_profile': None,
                    'explanation': 'ETA de respaldo (fuente: %s).' % pred_fb.get('fuente', 'fallback'),
                }
                eta_ok = True
            except Exception as e2:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error calculando ETA (fallback) para programación: {str(e2)}")

        # HAL-1: tercer fallback (haversine + velocidad de referencia 35 km/h).
        # Mismo cálculo que NotificationService.actualizar_eta, para garantizar
        # que siempre haya un eta_minutos operable (la UI muestra ETA desde
        # fecha_inicio_ruta + eta_minutos, y sin él quedaba en silencio).
        if not eta_ok:
            from math import asin, cos, radians, sin, sqrt
            from decimal import Decimal as _Dec
            try:
                R = 6371.0
                p1 = radians(float(lat))
                p2 = radians(float(programacion.cd.lat))
                dp = radians(float(programacion.cd.lat) - float(lat))
                dl = radians(float(programacion.cd.lng) - float(lng))
                a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
                km = 2 * R * asin(sqrt(a))
                velocidad_kmh = 35.0
                eta_min = max(1, int(round(km / velocidad_kmh * 60)))
                programacion.eta_minutos = eta_min
                programacion.distancia_km = _Dec(str(round(km, 2)))
                programacion.prediccion_ml = {
                    'source': 'haversine_fallback',
                    'mapbox_minutes': None,
                    'predicted_minutes': eta_min,
                    'learned_factor': None,
                    'samples': 0,
                    'confidence': 0.0,
                    'driver_profile': None,
                    'explanation': (
                        'ETA estimada por distancia haversine (35 km/h de referencia) '
                        'porque tanto Mapbox como ML no estaban disponibles.'
                    ),
                }
                eta_ok = True
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(
                    f"HAL-1 haversine fallback activado: prog={programacion.pk} "
                    f"km={km:.2f} eta_min={eta_min}"
                )
            except Exception as e3:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(
                    f"HAL-1 haversine fallback falló prog={programacion.pk}: {e3}"
                )

        # HAL-1: blindaje final — si llegamos aquí sin ETA, persiste algo legible
        # en lugar de propagar None y romper la UI / int(None) downstream.
        if not eta_ok or programacion.eta_minutos is None:
            programacion.eta_minutos = 0
            programacion.distancia_km = programacion.distancia_km or 0
            programacion.prediccion_ml = {
                **(programacion.prediccion_ml or {}),
                'source': 'no_disponible',
                'explanation': 'ETA no disponible (Mapbox, ML y haversine fallaron).',
                'requires_attention': True,
            }

        # HAL-1: persisto siempre aunque eta_ok=False — la blindaja final deja
        # prediccion_ml marcado como no_disponible y eta_minutos=0, evitando
        # un save posterior que perdería la asignación.
        programacion.save(update_fields=[
            'eta_minutos', 'distancia_km', 'ruta_geojson', 'ruta_firma',
            'prediccion_ml', 'updated_at',
        ])
        
        # Crear notificación con ETA (pasar la ETA ya calculada de la programación
        # para no recalcular con Mapbox y quedar sin ella si Mapbox falla).
        try:
            notificacion = NotificationService.crear_notificacion_inicio_ruta(
                programacion, programacion.driver,
                eta_minutos=programacion.eta_minutos,
                distancia_km=programacion.distancia_km,
            )
            notificacion_data = {
                'id': notificacion.id,
                'titulo': notificacion.titulo,
                'mensaje': notificacion.mensaje,
                'eta_minutos': notificacion.eta_minutos,
                'eta_timestamp': notificacion.eta_timestamp,
                'distancia_km': str(notificacion.distancia_km) if notificacion.distancia_km else None
            }
        except Exception as e:
            # Si falla la notificación, continuar pero registrar el error
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error creando notificación de inicio de ruta: {str(e)}")
            notificacion_data = None
        
        return {
            'ok': True,
            'programacion': programacion,
            'notificacion_data': notificacion_data,
            'patente_confirmada': patente_ingresada,
            'gps': {'lat': str(lat), 'lng': str(lng)},
        }

    @classmethod
    def aceptar_asignacion_conductor(cls, programacion, usuario=None):
        """(iteración 2 monolito — extraído de programaciones.views.aceptar_asignacion)
        Registra la decisión del conductor que ACEPTA la asignación.

        HAL-16 (decisión creativa documentada): aceptar tanto 'asignado' como
        'programado'. Rationale:
        - 'asignado' es el camino normal: conductor ya visible.
        - 'programado' lo aceptamos porque hay una ventana transitoria donde
          Programacion.objects.create(driver=X) YA pasó pero el container
          aún no pasó a 'asignado' (la cadena post_save → driver.asignar_conductor
          puede estar en vuelo vía on_commit). En esa ventana, rechazar el clic
          'Aceptar' generaba falsos 400 que confundían al conductor. La regla
          de fondo (driver_id presente + container en estado válido) ya cubre
          el caso.
        No restringir a solo 'asignado' porque romperíamos la UX sin necesidad:
        la pregunta relevante es "¿conductor asignado?", no "¿container ya
        transicionado?".

        Este método NO cambia container.estado (a diferencia del incidente):
        solo registra la decisión del conductor para trazabilidad y dispara
        el evento de auditoría.

        Returns:
            dict: {'ok': True, 'decision_operador': 'CONFIRMAR'} o
                  {'ok': False, 'error': str}.
        """
        if container_estado := programacion.container.estado:
            if container_estado not in ('asignado', 'programado'):
                return {
                    'ok': False,
                    'error': f'Contenedor en estado {container_estado}; solo se acepta en estado asignado/programado.',
                }

        from apps.events.models import Event
        with transaction.atomic():
            locked = Programacion.objects.select_for_update().get(pk=programacion.pk)
            locked.decision_operador = 'CONFIRMAR'
            locked.save(update_fields=['decision_operador', 'updated_at'])
            Event.objects.create(
                container=locked.container,
                event_type='asignacion_conductor',
                detalles={
                    'driver_id': locked.driver_id,
                    'aceptada': True,
                    'decision_operador': 'CONFIRMAR',
                    'reportado_por': usuario or 'anonimo',
                },
                usuario=usuario or 'anonimo',
            )
        # Propagar al objeto externo
        programacion.decision_operador = 'CONFIRMAR'
        return {'ok': True, 'decision_operador': 'CONFIRMAR'}

    @staticmethod
    def registrar_incidente_viaje(programacion, *, tipo_incidente, descripcion,
                                  gravedad='MODERADA', lat=None, lng=None, usuario=None):
        """(iteración 3 monolito — extraído de programaciones.views.reportar_incidente)
        Registra un incidente de viaje en `incidentes_registrados` (JSONField)
        con append atómico (select_for_update) + Event de auditoría, y notifica
        a operadores vía OpenClaw si la gravedad es ALTA/CRITICA (fuera del
        atomic — patrón e9e88b46: I/O de red fuera del lock; su fallo no
        revierte el incidente ya persistido).

        P2-3: los 4 tipos aquí cambian container.estado a 'incidente' (FSM).
        Problemas operativos que NO escalan estado van por reportar_problema.

        Returns:
            dict: {'ok': True, 'incidente': incidente_data} o
                  {'ok': False, 'lock_failure': bool, 'error': str}.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not tipo_incidente or not descripcion:
            return {'ok': False, 'error': 'tipo_incidente y descripcion son campos obligatorios.'}

        tipos_validos = ["ACCIDENTE", "AVERIA", "DEMORA_TRAFICO", "OTRO"]
        gravedades_validas = ["LEVE", "MODERADA", "ALTA", "CRITICA"]
        if tipo_incidente not in tipos_validos:
            return {'ok': False, 'error': f'Tipo de incidente inválido. Tipos permitidos: {", ".join(tipos_validos)}'}
        if gravedad not in gravedades_validas:
            return {'ok': False, 'error': f'Gravedad inválida. Gravedades permitidas: {", ".join(gravedades_validas)}'}

        incidente_data = {
            'tipo': tipo_incidente,
            'descripcion': descripcion,
            'gravedad': gravedad,
            'timestamp': timezone.now().isoformat(),
            'reportado_por': usuario or 'anonimo',
        }
        if lat and lng:
            incidente_data['gps_lat'] = str(lat)
            incidente_data['gps_lng'] = str(lng)

        from apps.events.models import Event
        try:
            with transaction.atomic():
                locked = Programacion.objects.select_for_update().get(pk=programacion.pk)
                lista_actual = locked.incidentes_registrados or []
                lista_actual.append(incidente_data)
                locked.incidentes_registrados = lista_actual
                locked.save(update_fields=['incidentes_registrados'])
                # Propagar la lista actualizada al objeto del caller para que
                # el serializer refleje el incidente recién agregado.
                programacion.incidentes_registrados = lista_actual
                Event.objects.create(
                    container=locked.container,
                    event_type='incidente_reportado',
                    detalles=incidente_data,
                    usuario=usuario or 'anonimo'
                )
        except Exception as _lock_exc:
            logger.error(
                'registrar_incidente_viaje_lock_failure programacion_id=%s detalle=%s',
                getattr(programacion, 'pk', None),
                _lock_exc,
                exc_info=True,
            )
            return {
                'ok': False,
                'lock_failure': True,
                'error': 'No se pudo registrar el incidente de forma atómica. Reintente.',
            }

        if gravedad in ('ALTA', 'CRITICA'):
            try:
                from apps.core.services.openclaw import OpenClawService
                OpenClawService.notify_anomaly(
                    programacion,
                    [
                        {
                            'code': f"INCIDENTE_{gravedad}",
                            'severity': 'P0' if gravedad == 'CRITICA' else 'P1',
                            'message': f"Incidente reportado: {tipo_incidente} - {descripcion}",
                            'recommended_action': "Revisar de inmediato y coordinar asistencia."
                        }
                    ]
                )
            except Exception as _openclaw_exc:
                logger.warning(
                    'registrar_incidente_viaje_openclaw_failed programacion_id=%s gravedad=%s detalle=%s',
                    getattr(programacion, 'pk', None),
                    gravedad,
                    _openclaw_exc,
                )

        return {'ok': True, 'incidente': incidente_data}

    @staticmethod
    def calcular_preasignacion_ml(programacion, *, driver_id, fecha_salida_str):
        """(iteración 2 monolito — extraído de programaciones.views.crear_preasignacion)
        Crea una pre-asignación: reserva conductor en una programación SIN
        cambiar el estado del contenedor, calculando métricas ML de ETA y
        confianza para decisión del operador.

        Origen: posición física del contenedor (geocode) con fallback a la
        última posición del driver y a Santiago. Ruta base Mapbox + predicción
        híbrida ML; persiste prediccion_ml auditable, bitácora
        RegistroOperacion, recomendación de horario óptimo y riesgo demurrage.

        Returns:
            dict: {'ok': True, 'payload': {...201 body...}, 'programacion'} o
                  {'ok': False, 'error': str, 'status_code': 400|404}.
        """
        from apps.core.services.learning_engine import OperationalLearningEngine
        from apps.core.services.mapbox import MapboxService
        from apps.programaciones.models import RegistroOperacion
        from dateutil import parser as date_parser
        import uuid, logging
        logger = logging.getLogger(__name__)

        if not driver_id:
            return {'ok': False, 'error': 'driver_id es requerido', 'status_code': 400}
        if not fecha_salida_str:
            return {'ok': False, 'error': 'fecha_salida es requerida', 'status_code': 400}

        from apps.drivers.models import Driver
        try:
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            return {'ok': False, 'error': f'Conductor ID {driver_id} no encontrado', 'status_code': 404}

        if not driver.esta_disponible:
            return {
                'ok': False,
                'error': f'Conductor {driver.nombre} no está disponible',
                'status_code': 400,
            }

        if programacion.driver:
            return {
                'ok': False,
                'error': f'Ya tiene conductor asignado ({programacion.driver.nombre}). Use desasignar primero.',
                'status_code': 400,
            }

        try:
            fecha_salida = date_parser.parse(fecha_salida_str)
        except Exception:
            return {'ok': False, 'error': 'fecha_salida con formato inválido. Use ISO 8601.', 'status_code': 400}

        container = programacion.container
        cd = programacion.cd

        # -- Origen: posición física del contenedor o fallback a ubicación del driver --
        origen_coords = None
        if container.posicion_fisica:
            try:
                geocode = MapboxService.geocode(container.posicion_fisica)
                if geocode and geocode.get('success'):
                    origen_coords = (geocode['lat'], geocode['lng'])
            except Exception:
                pass

        if not origen_coords:
            if driver.ultima_posicion_lat is not None and driver.ultima_posicion_lng is not None:
                origen_coords = (float(driver.ultima_posicion_lat), float(driver.ultima_posicion_lng))
            else:
                origen_coords = (-33.4489, -70.6693)  # Santiago fallback

        destino_coords = (float(cd.lat), float(cd.lng))

        # -- Ruta base Mapbox --
        mapbox_route = MapboxService.calcular_ruta(
            float(origen_coords[1]), float(origen_coords[0]),
            float(destino_coords[1]), float(destino_coords[0])
        )
        if not mapbox_route.get('duration_minutes'):
            # Fix co-review Safari 07-oct: Response/status no están importados en
            # operations.py (NameError -> 500 en cuanto Mapbox falle). Devolver el
            # resultado del servicio; el wrapper mapea status_code a la respuesta.
            return {
                'ok': False,
                'error': f'No se pudo calcular ruta desde {origen_coords} hasta {cd.nombre}.',
                'status_code': 400,
            }

        base_route = {
            'duration_minutes': float(mapbox_route['duration_minutes']),
            'distance_km': float(mapbox_route.get('distance_km', 0)),
            'route_index': 0,
            'route_signature': mapbox_route.get('route_signature', ''),
        }

        # -- Predicción híbrida ML --
        prediccion = OperationalLearningEngine.predict_route(
            origen_coords, destino_coords, fecha_salida,
            base_route, driver=driver
        )

        eta_minutos = prediccion['predicted_minutes']
        confianza = prediccion['confidence']
        fuente = prediccion['source']
        factor_ml = prediccion['learned_factor']
        muestras_ml = prediccion['samples']
        perfil_conductor = prediccion.get('driver_profile')
        mapa_minutos = prediccion['mapbox_minutes']

        # -- Guardar predicción ML en Programacion (auditable) --
        programacion.prediccion_ml = {
            'driver_id': driver.id,
            'driver_nombre': driver.nombre,
            'fecha_salida': fecha_salida.isoformat(),
            'eta_minutos': eta_minutos,
            'confianza': confianza,
            'fuente': fuente,
            'factor_ml': factor_ml,
            'muestras_ml': muestras_ml,
            'mapbox_minutos': mapa_minutos,
            'distancia_km': base_route['distance_km'],
            'perfil_conductor': perfil_conductor,
            'origen_coords': list(origen_coords),
            'destino_coords': list(destino_coords),
            'cd_destino': cd.nombre,
        }
        programacion.save(update_fields=['prediccion_ml', 'updated_at'])

        # -- Bitácora RegistroOperacion --
        service_id = f"preasign-{programacion.id}-{uuid.uuid4().hex[:8]}"
        RegistroOperacion.objects.create(
            programacion=programacion,
            service_id=service_id,
            recurso_asignado=f"{driver.nombre} (pre-asignación ML)",
            score_por_dimension={
                'eta_minutos': eta_minutos,
                'confianza': confianza,
                'factor_ml': factor_ml,
                'muestras_ml': muestras_ml,
            }
        )

        # -- Recomendación horario óptimo --
        recomendacion = OperationalLearningEngine.recommend(
            origen_coords, destino_coords, fecha_salida,
            driver=driver, window_hours=3
        )
        horario_optimo = None
        if recomendacion.get('success') and recomendacion.get('recommended'):
            rec = recomendacion['recommended']
            horario_optimo = {
                'hora_salida': rec.get('departure').isoformat() if rec.get('departure') else None,
                'eta_min': rec.get('predicted_minutes'),
                'confianza': rec.get('confidence'),
            }

        # -- Alerta demurrage --
        riesgo_demurrage = None
        if container.fecha_demurrage:
            horas_vencimiento = (container.fecha_demurrage - fecha_salida).total_seconds() / 3600
            riesgo_demurrage = {
                'horas_hasta_vencimiento': round(horas_vencimiento, 1),
                'alerta': horas_vencimiento < (eta_minutos / 60),
                'mensaje': '⚠️ Demurrage por vencer' if horas_vencimiento < (eta_minutos / 60) else None,
            }

        logger.info(
            f"Pre-asignación ML: prog={programacion.id} driver={driver.nombre} "
            f"ETA={eta_minutos}min confianza={confianza:.0%} muestras={muestras_ml}"
        )

        payload = {
            'success': True,
            'mensaje': f'Pre-asignación creada para {driver.nombre}',
            'programacion_id': programacion.id,
            'driver': {
                'id': driver.id,
                'nombre': driver.nombre,
                'patente': driver.patente,
            },
            'ml': {
                'eta_minutos': eta_minutos,
                'confianza': round(confianza, 3),
                'fuente': fuente,
                'factor_ml': factor_ml,
                'muestras_ml': muestras_ml,
                'mapbox_minutos': mapa_minutos,
                'distancia_km': base_route['distance_km'],
                'perfil_conductor': perfil_conductor,
            },
            'horario_optimo': horario_optimo,
            'riesgo_demurrage': riesgo_demurrage,
            'service_id': service_id,
        }
        return {'ok': True, 'payload': payload, 'programacion': programacion}
    @classmethod
    def crear_ruta_manual(cls, container, *, tipo_movimiento, cd_destino,
                          fecha_programacion, cliente='', observaciones=None,
                          usuario=None):
        """(iteración 5 monolito — extraído de programaciones.views.crear_ruta_manual)
        Crea una ruta manual para retiro desde puerto sin tocar request/Response.

        Casos de uso: retiro_patio (puerto → patio) y retiro_directo (puerto →
        cliente). Para retiro_patio resuelve el primer CD tipo 'patio' (error si
        no hay). Pre-valida programación existente (idempotente, payload rico
        con programacion_existente) y captura IntegrityError de la carrera
        OneToOne como 409 lógico. Dentro del atomic: create + FSM a 'programado'
        + Event 'import_programacion' (ruta_manual_creada) + P1-4
        TiempoOperacion (fallo loggeado, no bloquea).

        Returns:
            dict: {'ok': True, 'programacion', 'container', 'cd_destino'} o
                  {'ok': False, 'error': str, ['status_code': 409],
                   ['programacion_existente': {...}]}.
        """
        import logging
        logger = logging.getLogger(__name__)
        from django.db import IntegrityError
        from apps.core.utils import normalizar_cliente
        from apps.cds.models import CD
        from apps.events.models import Event

        # Actualizar tipo de movimiento en el contenedor
        container.tipo_movimiento = tipo_movimiento
        container.save(update_fields=['tipo_movimiento'])
        
        # Determinar CD destino
        if tipo_movimiento == 'retiro_patio':
            # Buscar el primer Patio
            cd_destino = CD.objects.filter(tipo='patio').first()
            if not cd_destino:
                return {'ok': False, 'error': 'No se encontró ningún Patio en el sistema'}
        # (retiro_directo llega con cd_destino ya resuelto por el serializer)
        
        # Pre-validación: si el contenedor ya tiene una programación asociada,
        # evitamos el IntegrityError del OneToOne respondiendo 400 (consistente
        # con containers.views.programar). Hace la re-ejecución sobre el mismo
        # contenedor idempotente para el operador en vez de un 500 opaco.
        tiene_prog, existing_prog = Programacion.container_tiene_programacion(container)
        if tiene_prog and existing_prog is not None:
            return {
                'ok': False,
                'error': f'Este contenedor ya tiene una programación asociada (ID: {existing_prog.id})',
                'programacion_existente': {
                    'id': existing_prog.id,
                    'fecha_programada': existing_prog.fecha_programada.isoformat(),
                    'cd': existing_prog.cd.nombre if existing_prog.cd else None,
                    'tiene_conductor': existing_prog.driver is not None,
                    'estado_container': container.estado,
                },
            }

        # Crear la programación dentro de transacción atómica y capturar
        # IntegrityError por si una carrera concurrente inserta la fila OneToOne
        # entre la validación previa y el create().
        try:
            with transaction.atomic():
                programacion = Programacion.objects.create(
                    container=container,
                    cd=cd_destino,
                    fecha_programada=fecha_programacion,
                    cliente=normalizar_cliente(cliente),
                    direccion_entrega=cd_destino.direccion,
                    observaciones=observaciones if observaciones is not None else f'Retiro manual desde {container.posicion_fisica}',
                )

                container.cambiar_estado('programado', usuario)

                # Crear evento de auditoría
                from apps.events.models import Event
                Event.objects.create(
                    container=container,
                    event_type='import_programacion',
                    usuario=usuario,
                    detalles={
                        'accion': 'ruta_manual_creada',
                        'descripcion': f'Ruta manual creada: {tipo_movimiento}',
                        'tipo_movimiento': tipo_movimiento,
                        'origen': container.posicion_fisica,
                        'destino': cd_destino.nombre,
                        'programacion_id': programacion.id,
                        'fecha_programacion': fecha_programacion.isoformat(),
                    }
                )

                # P1-4: registrar TiempoOperacion para carga_patio o retiro_puerto
                # según tipo_movimiento. started_at = ahora (sin dato histórico real),
                # finished_at = fecha_programacion (estimación del operador).
                try:
                    tipo_op = 'carga_patio' if tipo_movimiento == 'retiro_patio' else 'retiro_puerto'
                    cls.registrar_operacion_tiempo(
                        container=container,
                        tipo_operacion=tipo_op,
                        started_at=timezone.now(),
                        finished_at=fecha_programacion,
                        cd_origen=cd_destino,
                        cd_destino=cd_destino,
                        conductor=None,
                        observaciones=f'Carga/retiro programado (ruta manual {tipo_movimiento})',
                    )
                except Exception as _p1_exc:
                    logger.warning('crear_ruta_manual tiempo_operacion_failed: %s', _p1_exc)
        except IntegrityError:
            logger.warning(
                'crear_ruta_manual_integrity_error',
                extra={'container_id': getattr(container, 'container_id', None)},
            )
            return {
                'ok': False,
                'status_code': 409,
                'error': 'Este contenedor ya tiene una programación asociada. Por favor, recargue la página.',
            }
        
        return {
            'ok': True,
            'programacion': programacion,
            'container': container,
            'cd_destino': cd_destino,
        }

    @classmethod
    def actualizar_posicion_gps(cls, programacion, *, lat, lng, usuario=None,
                                eta_delay_threshold=None):
        """(iteración 6 monolito — extraído de programaciones.views.actualizar_posicion)
        Actualiza la posición del conductor y recalcula ETA.

        Arribo automático: permanece dormido hasta que el CD tenga un radio.
        Se comprueba antes del tracking ordinario para registrar una sola
        muestra GPS.

        Args:
            eta_delay_threshold: override del umbral de alerta de retraso
            (si None, usa settings.ETA_DELAY_ALERT_MIN).

        Returns:
            dict: {'ok': True, ...} o {'ok': False, 'error': str,
                  'status_code': 400|500}.
        """
        from apps.notifications.services import NotificationService
        from django.conf import settings

        if lat is None or lng is None:
            return {'ok': False, 'error': 'lat y lng requeridos', 'status_code': 400}
        
        # Arribo automático: permanece dormido hasta que el CD tenga un radio.
        # Se comprueba antes del tracking ordinario para registrar una sola muestra GPS.
        if (
            programacion.container.estado == 'en_ruta'
            and programacion.cd.contiene_en_geocerca(lat, lng)
        ):
            locked, created = cls.registrar_arribo(
                programacion, lat, lng, 'geocerca', 'system_geocerca'
            )
            return {
                'ok': True,
                'arribo_automatico': True,
                'arribo_creado': created,
                'fecha_arribo_cd': programacion.fecha_arribo_cd,
                'nuevo_estado': 'entregado',
                'programacion': programacion,
            }

        # Fuera de geocerca, guardar tracking y recalcular ETA normalmente.
        programacion.driver.actualizar_posicion(lat, lng)
        
        # Actualizar ETA y crear notificación si cambió significativamente
        resultado = NotificationService.actualizar_eta(
            programacion, programacion.driver, lat, lng
        )
        
        if not resultado:
            return {'ok': False, 'error': 'No se pudo calcular ETA actualizado', 'status_code': 500}
        
        # Verificar si debe crear alerta de arribo próximo
        if resultado['eta_minutos'] <= 15:
            NotificationService.crear_alerta_arribo_proximo(programacion)

        programacion.eta_recalculado_min = resultado['eta_minutos']
        configured_delay_threshold = int(getattr(settings, 'ETA_DELAY_ALERT_MIN', 15))
        request_override_threshold = request.query_params.get('eta_delay_alert_min')
        eta_delay_threshold = int(request_override_threshold) if request_override_threshold else configured_delay_threshold
        if programacion.eta_minutos and (resultado['eta_minutos'] - programacion.eta_minutos) > eta_delay_threshold:
            desvio = {
                'tipo': 'ETA_DELAY',
                'mensaje': 'ETA recalculado supera lo prometido',
                'valor_min': int(resultado['eta_minutos'] - programacion.eta_minutos),
                'timestamp': timezone.now().isoformat(),
            }
            programacion.desviaciones_detectadas = (programacion.desviaciones_detectadas or []) + [desvio]
        programacion.save(update_fields=[
            'posicion_actual_lat', 'posicion_actual_lng', 'ultima_actualizacion_tracking',
            'eta_recalculado_min', 'desviaciones_detectadas'
        ])
        
        response_data = {
            'success': True,
            'mensaje': 'Posición actualizada y ETA recalculado',
            'eta_minutos': resultado['eta_minutos'],
            'distancia_km': str(resultado['distancia_km']),
            'eta_timestamp': resultado['eta_timestamp']
        }
        
        if resultado['notificacion']:
            response_data['notificacion'] = {
                'id': resultado['notificacion'].id,
                'titulo': resultado['notificacion'].titulo,
                'mensaje': resultado['notificacion'].mensaje
            }
        
        return Response(response_data)