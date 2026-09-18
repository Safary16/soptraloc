"""
Mantenimiento diario de la operación TMS.

Ejecutar 1 vez al día (ej: 05:30) vía cron/hook del host:
    python manage.py mantenimiento_diario

Resuelve (hallazgos auditoría 2026-09-18):
- E: reset de num_entregas_dia (sin reset automático, los conductores se
     auto-bloquean con el contador del día anterior).
- H: retención de DriverLocation (crecía sin límite).
- Limpieza: archiva notificaciones enviadas/leídas antiguas.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.drivers.models import Driver, DriverLocation
from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = "Mantenimiento diario: reset de entregas, retención de posiciones y limpieza de notificaciones."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias-retencion-posiciones',
            type=int,
            default=30,
            help='Días de historial de posiciones a conservar (default: 30)',
        )
        parser.add_argument(
            '--dias-notificaciones',
            type=int,
            default=7,
            help='Días de antigüedad para archivar notificaciones (default: 7)',
        )

    def handle(self, *args, **options):
        # --- E: reset de entregas diarias -----------------------------------
        reseteados = Driver.objects.exclude(num_entregas_dia=0).update(num_entregas_dia=0)
        self.stdout.write(self.style.SUCCESS(f'[entregas] reseteadas: {reseteados} conductores'))

        # --- H: retención de DriverLocation ----------------------------------
        limite_posiciones = timezone.now() - timedelta(days=options['dias_retencion_posiciones'])
        purgadas, _ = DriverLocation.objects.filter(timestamp__lt=limite_posiciones).delete()
        self.stdout.write(self.style.SUCCESS(
            f'[posiciones] purgadas {purgadas} registros anteriores a {options["dias_retencion_posiciones"]} días'
        ))

        # --- Limpieza de notificaciones antiguas ------------------------------
        archivadas = NotificationService.limpiar_notificaciones_antiguas(dias=options['dias_notificaciones'])
        self.stdout.write(self.style.SUCCESS(f'[notificaciones] archivadas: {archivadas}'))