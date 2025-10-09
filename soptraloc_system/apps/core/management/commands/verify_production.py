"""
Management command para verificar que la configuración de producción está completa.
Verifica: direcciones reales, Mapbox API, conductores, migraciones.
Uso: python manage.py verify_production
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.routing.locations_catalog import LOCATIONS_CATALOG
from apps.drivers.models import Driver
from apps.core.models import Location


class Command(BaseCommand):
    help = 'Verifica que la configuración de producción esté completa y correcta'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('VERIFICACIÓN DE PRODUCCIÓN - SOPTRALOC TMS'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))
        
        errors = []
        warnings = []
        
        # 1. Verificar Mapbox API Key
        self.stdout.write('1️⃣  Verificando configuración de Mapbox...')
        mapbox_key = getattr(settings, 'MAPBOX_ACCESS_TOKEN', None)
        if not mapbox_key:
            errors.append('❌ MAPBOX_ACCESS_TOKEN no configurado')
        elif mapbox_key.startswith('pk.'):
            self.stdout.write(self.style.SUCCESS(f'   ✅ Mapbox API configurado: {mapbox_key[:20]}...'))
        else:
            warnings.append('⚠️  MAPBOX_ACCESS_TOKEN no tiene formato válido')
        
        # 2. Verificar direcciones reales en el catálogo
        self.stdout.write('\n2️⃣  Verificando direcciones reales en catálogo...')
        critical_locations = ['CD_PENON', 'CD_QUILICURA', 'CCTI', 'CD_CAMPOS', 'CD_PUERTO_MADERO']
        
        for loc_code in critical_locations:
            if loc_code in LOCATIONS_CATALOG:
                loc = LOCATIONS_CATALOG[loc_code]
                if loc.latitude and loc.longitude:
                    self.stdout.write(
                        f'   ✅ {loc.name:30s} → {loc.address[:40]:40s} '
                        f'({loc.latitude:.4f}, {loc.longitude:.4f})'
                    )
                else:
                    warnings.append(f'⚠️  {loc.name} no tiene coordenadas GPS')
            else:
                errors.append(f'❌ {loc_code} no existe en LOCATIONS_CATALOG')
        
        # 3. Verificar que las Location estén en la base de datos
        self.stdout.write('\n3️⃣  Verificando ubicaciones en base de datos...')
        db_locations = Location.objects.count()
        self.stdout.write(f'   📍 Total de ubicaciones en DB: {db_locations}')
        
        for loc_code in critical_locations:
            try:
                db_loc = Location.objects.get(code=loc_code)
                if db_loc.latitude and db_loc.longitude:
                    self.stdout.write(f'   ✅ {db_loc.name:30s} → GPS: ({db_loc.latitude:.4f}, {db_loc.longitude:.4f})')
                else:
                    warnings.append(f'⚠️  {db_loc.name} en DB sin coordenadas GPS')
            except Location.DoesNotExist:
                errors.append(f'❌ {loc_code} no existe en DB - ejecutar load_initial_times')
        
        # 4. Verificar conductores
        self.stdout.write('\n4️⃣  Verificando conductores...')
        total_drivers = Driver.objects.count()
        active_drivers = Driver.objects.filter(is_active=True).count()
        drivers_with_assignments = Driver.objects.filter(assignments__isnull=False).distinct().count()
        
        self.stdout.write(f'   👨‍💼 Total de conductores: {total_drivers}')
        self.stdout.write(f'   ✅ Conductores activos: {active_drivers}')
        self.stdout.write(f'   📋 Con asignaciones: {drivers_with_assignments}')
        
        if total_drivers > 100:
            warnings.append(f'⚠️  Hay {total_drivers} conductores (se esperan ~50). Ejecutar aggressive_cleanup')
        elif total_drivers > 200:
            errors.append(f'❌ CRÍTICO: {total_drivers} conductores. Ejecutar aggressive_cleanup URGENTE')
        
        # 5. Verificar variables de entorno críticas
        self.stdout.write('\n5️⃣  Verificando variables de entorno...')
        env_vars = {
            'DATABASE_URL': 'Base de datos',
            'REDIS_URL': 'Redis (Celery)',
            'SECRET_KEY': 'Secret Key Django',
            'MAPBOX_ACCESS_TOKEN': 'Mapbox API',
        }
        
        for var, description in env_vars.items():
            value = getattr(settings, var.replace('_URL', '').replace('DATABASE', 'DATABASES'), None)
            if var == 'DATABASE_URL':
                value = settings.DATABASES.get('default', {}).get('ENGINE')
            elif var == 'SECRET_KEY':
                value = settings.SECRET_KEY
            elif var == 'REDIS_URL':
                # Check Celery broker
                value = getattr(settings, 'CELERY_BROKER_URL', None)
            
            if value:
                display_value = str(value)[:30] + '...' if len(str(value)) > 30 else str(value)
                self.stdout.write(f'   ✅ {description:20s} → {display_value}')
            else:
                errors.append(f'❌ {description} no configurado')
        
        # 6. Resumen
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.WARNING('RESUMEN'))
        self.stdout.write('='*80 + '\n')
        
        if errors:
            self.stdout.write(self.style.ERROR(f'\n❌ ERRORES CRÍTICOS ({len(errors)}):'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'   {error}'))
        
        if warnings:
            self.stdout.write(self.style.WARNING(f'\n⚠️  ADVERTENCIAS ({len(warnings)}):'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'   {warning}'))
        
        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS('\n✅ TODO VERIFICADO - Sistema listo para producción\n'))
        elif not errors:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Sistema funcional con {len(warnings)} advertencias\n'))
        else:
            self.stdout.write(self.style.ERROR(f'\n❌ Sistema con {len(errors)} errores críticos\n'))
            self.stdout.write(self.style.ERROR('Ejecutar comandos de corrección antes de usar en producción.\n'))
        
        # 7. Acciones recomendadas
        if errors or warnings:
            self.stdout.write(self.style.WARNING('ACCIONES RECOMENDADAS:'))
            if total_drivers > 100:
                self.stdout.write('   → python manage.py aggressive_cleanup --dry-run')
                self.stdout.write('   → python manage.py aggressive_cleanup --force --keep=50')
            if db_locations < 5:
                self.stdout.write('   → python manage.py load_initial_times')
            self.stdout.write('')
