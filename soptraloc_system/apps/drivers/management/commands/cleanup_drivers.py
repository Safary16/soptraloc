"""
Management command para limpiar conductores sin asignaciones en producción.
Uso: python manage.py cleanup_drivers [--dry-run] [--force]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.drivers.models import Driver, Assignment


class Command(BaseCommand):
    help = 'Elimina conductores sin asignaciones y sin actividad reciente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se eliminaría sin hacer cambios',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecuta la limpieza sin pedir confirmación',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Días de inactividad para considerar un conductor eliminable (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        days = options['days']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('LIMPIEZA DE CONDUCTORES'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))
        
        # Mostrar estadísticas actuales
        total_drivers = Driver.objects.count()
        active_drivers = Driver.objects.filter(is_active=True).count()
        
        self.stdout.write(f"📊 Total de conductores: {total_drivers}")
        self.stdout.write(f"✅ Conductores activos: {active_drivers}")
        self.stdout.write(f"❌ Conductores inactivos: {total_drivers - active_drivers}\n")
        
        # Identificar conductores a eliminar
        # Criterio: sin asignaciones Y sin actividad reciente
        drivers_with_assignments = Driver.objects.filter(
            assignments__isnull=False
        ).distinct().values_list('id', flat=True)
        
        drivers_with_recent_activity = Driver.objects.filter(
            updated_at__gte=cutoff_date
        ).values_list('id', flat=True)
        
        # Conductores elegibles para eliminación
        deletable_drivers = Driver.objects.exclude(
            id__in=list(drivers_with_assignments) + list(drivers_with_recent_activity)
        )
        
        deletable_count = deletable_drivers.count()
        
        if deletable_count == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ No hay conductores que eliminar.\n'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n🗑️  Conductores elegibles para eliminación: {deletable_count}'))
        self.stdout.write(f"   - Sin asignaciones registradas")
        self.stdout.write(f"   - Sin actividad desde hace {days} días\n")
        
        # Mostrar muestra de conductores a eliminar
        sample = deletable_drivers[:10].values_list('nombre', 'rut', 'created_at')
        self.stdout.write(self.style.WARNING('Muestra (primeros 10):'))
        for nombre, rut, created in sample:
            self.stdout.write(f"   - {nombre} (RUT: {rut}, creado: {created.strftime('%Y-%m-%d')})")
        
        if deletable_count > 10:
            self.stdout.write(f"   ... y {deletable_count - 10} más\n")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ DRY RUN - No se realizaron cambios.\n'))
            return
        
        # Confirmar antes de eliminar
        if not force:
            self.stdout.write(self.style.ERROR('\n⚠️  ADVERTENCIA: Esta acción es IRREVERSIBLE'))
            confirm = input(f'\n¿Eliminar {deletable_count} conductores? Escriba "SI" para confirmar: ')
            if confirm != 'SI':
                self.stdout.write(self.style.ERROR('\n❌ Operación cancelada.\n'))
                return
        
        # Eliminar conductores en transacción
        try:
            with transaction.atomic():
                deleted_count, _ = deletable_drivers.delete()
                
                self.stdout.write(self.style.SUCCESS(f'\n✅ Eliminados {deleted_count} conductores exitosamente.'))
                
                # Mostrar estadísticas finales
                remaining = Driver.objects.count()
                self.stdout.write(self.style.SUCCESS(f'📊 Conductores restantes: {remaining}\n'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error durante la eliminación: {str(e)}\n'))
            raise
