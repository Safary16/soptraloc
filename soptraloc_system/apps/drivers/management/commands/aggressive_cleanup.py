"""
Management command para limpieza AGRESIVA de conductores.
Mantiene solo los 50 conductores con información más completa.
Uso: python manage.py aggressive_cleanup [--dry-run] [--force] [--keep=50]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Q
from apps.drivers.models import Driver


class Command(BaseCommand):
    help = 'Elimina conductores dejando solo los 50 con más información completa'

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
            '--keep',
            type=int,
            default=50,
            help='Número de conductores a mantener (default: 50)',
        )

    def calculate_completeness_score(self, driver):
        """Calcula un puntaje de completitud para un conductor"""
        score = 0
        
        # Campos básicos (1 punto cada uno)
        if driver.nombre and len(driver.nombre.strip()) > 3:
            score += 1
        if driver.rut and len(driver.rut.strip()) > 5:
            score += 1
        if driver.telefono and len(driver.telefono.strip()) > 5:
            score += 1
        if driver.email and '@' in driver.email:
            score += 1
        if driver.direccion and len(driver.direccion.strip()) > 5:
            score += 1
        
        # Campos de licencia (2 puntos cada uno)
        if driver.licencia_numero:
            score += 2
        if driver.licencia_tipo:
            score += 2
        if driver.licencia_vencimiento:
            score += 2
        
        # Estado activo (1 punto)
        if driver.is_active:
            score += 1
        
        # Asignaciones (5 puntos por tener al menos una)
        assignment_count = driver.assignments.count()
        if assignment_count > 0:
            score += 5
        if assignment_count > 5:
            score += 3  # Bonus por múltiples asignaciones
        
        # Vehículo asignado (3 puntos)
        if hasattr(driver, 'vehicle') and driver.vehicle:
            score += 3
        
        # Datos adicionales
        if driver.comuna:
            score += 1
        if driver.fecha_nacimiento:
            score += 1
        if driver.contacto_emergencia:
            score += 1
        
        return score

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        keep_count = options['keep']
        
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('LIMPIEZA AGRESIVA DE CONDUCTORES'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))
        
        # Estadísticas iniciales
        total_drivers = Driver.objects.count()
        self.stdout.write(f"📊 Total de conductores en DB: {total_drivers}")
        
        if total_drivers <= keep_count:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Solo hay {total_drivers} conductores, no es necesario limpiar.\n'))
            return
        
        # Calcular puntaje de completitud para todos los conductores
        self.stdout.write(f"\n🔍 Analizando completitud de {total_drivers} conductores...")
        
        # Prefetch assignments para optimizar
        all_drivers = Driver.objects.prefetch_related('assignments').all()
        
        driver_scores = []
        for driver in all_drivers:
            score = self.calculate_completeness_score(driver)
            driver_scores.append((driver, score))
        
        # Ordenar por puntaje (mayor a menor)
        driver_scores.sort(key=lambda x: (x[1], x[0].created_at), reverse=True)
        
        # Separar los que se mantienen vs se eliminan
        to_keep = driver_scores[:keep_count]
        to_delete = driver_scores[keep_count:]
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Se mantendrán {len(to_keep)} conductores con mejor información:'))
        self.stdout.write('='*80)
        for i, (driver, score) in enumerate(to_keep[:10], 1):
            assignment_count = driver.assignments.count()
            self.stdout.write(
                f"{i:2d}. {driver.nombre[:30]:30s} | Score: {score:2d} | "
                f"RUT: {driver.rut or 'N/A':12s} | Asignaciones: {assignment_count}"
            )
        if len(to_keep) > 10:
            self.stdout.write(f"    ... y {len(to_keep) - 10} más\n")
        
        self.stdout.write(self.style.ERROR(f'\n🗑️  Se eliminarán {len(to_delete)} conductores:'))
        self.stdout.write('='*80)
        for i, (driver, score) in enumerate(to_delete[:10], 1):
            assignment_count = driver.assignments.count()
            self.stdout.write(
                f"{i:2d}. {driver.nombre[:30]:30s} | Score: {score:2d} | "
                f"RUT: {driver.rut or 'N/A':12s} | Asignaciones: {assignment_count}"
            )
        if len(to_delete) > 10:
            self.stdout.write(f"    ... y {len(to_delete) - 10} más\n")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ DRY RUN - No se realizaron cambios.\n'))
            return
        
        # Confirmar antes de eliminar
        if not force:
            self.stdout.write(self.style.ERROR('\n⚠️  ADVERTENCIA: Esta acción es IRREVERSIBLE'))
            self.stdout.write(self.style.ERROR(f'Se eliminarán {len(to_delete)} conductores de {total_drivers} totales.'))
            confirm = input(f'\n¿Continuar? Escriba "ELIMINAR" para confirmar: ')
            if confirm != 'ELIMINAR':
                self.stdout.write(self.style.ERROR('\n❌ Operación cancelada.\n'))
                return
        
        # Eliminar conductores en transacción
        try:
            with transaction.atomic():
                drivers_to_delete = [d[0].id for d in to_delete]
                deleted_count, details = Driver.objects.filter(id__in=drivers_to_delete).delete()
                
                self.stdout.write(self.style.SUCCESS(f'\n✅ Eliminados {deleted_count} conductores exitosamente.'))
                self.stdout.write(f'   Detalles: {details}')
                
                # Estadísticas finales
                remaining = Driver.objects.count()
                self.stdout.write(self.style.SUCCESS(f'\n📊 Conductores restantes: {remaining}'))
                self.stdout.write(self.style.SUCCESS('✅ Limpieza completada exitosamente.\n'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error durante la eliminación: {str(e)}\n'))
            raise
