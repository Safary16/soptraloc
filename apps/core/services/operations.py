"""Servicios transaccionales para cerrar operaciones y alimentar aprendizaje."""
from django.db import transaction
from django.utils import timezone

from apps.programaciones.models import Programacion, TiempoOperacion


class OperationalFlowService:
    @staticmethod
    def _record_discharge(programacion, started_at, finished_at, source):
        if TiempoOperacion.objects.filter(
            container=programacion.container, tipo_operacion='descarga_cd'
        ).exists():
            return None
        estimated = programacion.cd.tiempo_promedio_descarga_min or 60
        actual = max(1, int((finished_at - started_at).total_seconds() / 60))
        return TiempoOperacion.objects.create(
            cd=programacion.cd,
            conductor=programacion.driver,
            container=programacion.container,
            tipo_operacion='descarga_cd',
            tiempo_estimado_min=estimated,
            tiempo_real_min=actual,
            hora_inicio=started_at,
            hora_fin=finished_at,
            anomalia=actual > max(1, estimated) * 3,
            observaciones=f'Registro operacional automático: {source}',
        )

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
        return locked, True

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
