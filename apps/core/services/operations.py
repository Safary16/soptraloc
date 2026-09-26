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
        estimated = programacion.cd.tiempo_promedio_descarga_min or 60
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

        # P0-3: notificación visible para cliente/operador ('llegada' con prioridad alta).
        # Se crea DENTRO de la misma transacción para que un fallo de notificación
        # no quede con evento sin rastro, y para garantizar atomicidad con el
        # cambio de estado del contenedor. Si la app notifications no está
        # instalada se ignora silenciosamente.
        try:
            from apps.notifications.models import Notification
            hora_local = arrived_at.strftime('%H:%M')
            cd_nombre = locked.cd.nombre if locked.cd else 'CD'
            Notification.objects.create(
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
        except Exception as _notif_exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                'registrar_arribo_notification_failed container_id=%s detalle=%s',
                getattr(locked.container, 'container_id', None),
                _notif_exc,
                exc_info=True,
            )
        return locked, True

    @staticmethod
    def _lock_programacion(programacion):
        return Programacion.objects.select_for_update().select_related(
            'container', 'driver', 'cd'
        ).get(pk=programacion.pk)

    @classmethod
    def _auto_assign_empty_return(cls, programacion):
        """Crea (si aplica) una Programacion de retorno automático de un
        contenedor vacío 'fresco' desde el CD donde se soltó.

        Criterios:
        - Conductor recién liberado (driver_id presente y con capacidad).
        - Existe Container en estado='vacio', vacio_contabilizado=True,
          fecha_vacio >= now-2h, y mismo CD (Container.retorno_destino_cd
          o Container.cd_entrega == locked.cd).
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

        cutoff = timezone.now() - timedelta(hours=2)
        # Buscar contenedores vacíos frescos en el mismo CD donde soltó
        # el conductor. Compatibilidad: Container.retorno_destino_cd o
        # Container.cd_entrega equivalen al CD de la programación.
        from django.db.models import Q
        candidatos = Container.objects.filter(
            estado='vacio',
            vacio_contabilizado=True,
            fecha_vacio__gte=cutoff,
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
        # La asignación al conductor la dispara la señal post_save
        # (apps/programaciones/signals.py: trigger_automatic_assignment).
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
