"""
Management command que se ejecuta automáticamente después del deploy en Render.
Se llama desde render.yaml en el post_deploy hook.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from apps.drivers.models import Driver, Location
import sys


class Command(BaseCommand):
    help = 'Ejecuta todas las tareas post-deploy automáticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-cleanup',
            action='store_true',
            help='Omite la limpieza de conductores',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('POST-DEPLOY AUTOMÁTICO - SOPTRALOC TMS'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))
        
        errors = []
        
        # 1. Aplicar migraciones
        try:
            self.stdout.write('1️⃣  Aplicando migraciones...')
            call_command('migrate', '--noinput', verbosity=1)
            self.stdout.write(self.style.SUCCESS('   ✅ Migraciones aplicadas\n'))
        except Exception as e:
            error_msg = f'Error aplicando migraciones: {str(e)}'
            errors.append(error_msg)
            self.stdout.write(self.style.ERROR(f'   ❌ {error_msg}\n'))
        
        # 2. Cargar ubicaciones iniciales (si no existen)
        try:
            self.stdout.write('2️⃣  Verificando ubicaciones GPS...')
            location_count = Location.objects.count()
            
            if location_count < 5:
                self.stdout.write('   ⚠️  Pocas ubicaciones, cargando catálogo inicial...')
                call_command('load_initial_times', verbosity=0)
                new_count = Location.objects.count()
                self.stdout.write(self.style.SUCCESS(f'   ✅ Ubicaciones cargadas: {new_count}\n'))
            else:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Ubicaciones OK: {location_count}\n'))
        except Exception as e:
            error_msg = f'Error cargando ubicaciones: {str(e)}'
            errors.append(error_msg)
            self.stdout.write(self.style.ERROR(f'   ❌ {error_msg}\n'))
        
        # 3. Limpiar conductores excesivos (solo si hay más de 100)
        if not options['skip_cleanup']:
            try:
                self.stdout.write('3️⃣  Verificando conductores...')
                total_drivers = Driver.objects.count()
                self.stdout.write(f'   📊 Total de conductores: {total_drivers}')
                
                if total_drivers > 100:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  CRÍTICO: {total_drivers} conductores (esperado ~50)'))
                    self.stdout.write('   🗑️  Ejecutando limpieza automática...')
                    
                    # Ejecutar limpieza manteniendo los 50 mejores
                    call_command('aggressive_cleanup', '--force', '--keep=50', verbosity=1)
                    
                    remaining = Driver.objects.count()
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Limpieza completada: {remaining} conductores restantes\n'))
                elif total_drivers > 60:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Hay {total_drivers} conductores (se recomiendan ~50)'))
                    self.stdout.write('   💡 Ejecutar manualmente: python manage.py aggressive_cleanup --force --keep=50\n')
                else:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Cantidad de conductores OK\n'))
                    
            except Exception as e:
                error_msg = f'Error en limpieza de conductores: {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f'   ❌ {error_msg}\n'))
        else:
            self.stdout.write('3️⃣  Limpieza de conductores omitida (--skip-cleanup)\n')
        
        # 4. Recolectar archivos estáticos (para producción)
        try:
            self.stdout.write('4️⃣  Recolectando archivos estáticos...')
            call_command('collectstatic', '--noinput', '--clear', verbosity=0)
            self.stdout.write(self.style.SUCCESS('   ✅ Archivos estáticos recolectados\n'))
        except Exception as e:
            # No es crítico si falla
            self.stdout.write(self.style.WARNING(f'   ⚠️  Advertencia collectstatic: {str(e)}\n'))
        
        # 5. Verificación final
        self.stdout.write('5️⃣  Verificación final...')
        try:
            call_command('verify_production', verbosity=0)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  {str(e)}\n'))
        
        # Resumen
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.WARNING('RESUMEN POST-DEPLOY'))
        self.stdout.write('='*80 + '\n')
        
        if errors:
            self.stdout.write(self.style.ERROR(f'\n❌ Se encontraron {len(errors)} errores:\n'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'   - {error}'))
            self.stdout.write('\n')
            sys.exit(1)  # Salir con error para que Render lo detecte
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ POST-DEPLOY COMPLETADO EXITOSAMENTE'))
            self.stdout.write(self.style.SUCCESS('Sistema listo para producción\n'))
