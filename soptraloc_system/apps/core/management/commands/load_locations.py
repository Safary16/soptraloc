"""
Management command para cargar ubicaciones del catálogo a la base de datos.
"""
from django.core.management.base import BaseCommand
from apps.drivers.models import Location
from apps.routing.locations_catalog import LOCATIONS_CATALOG
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Carga las ubicaciones del catálogo SOPTRALOC a la base de datos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Actualiza ubicaciones existentes con nueva información'
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  CARGANDO UBICACIONES DEL CATÁLOGO SOPTRALOC'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for code, loc_info in LOCATIONS_CATALOG.items():
            try:
                # Buscar si ya existe (por code o por name)
                existing = Location.objects.filter(code=code).first() or \
                           Location.objects.filter(name=loc_info.name).first()
                
                if existing and not force:
                    self.stdout.write(
                        self.style.WARNING(f'⏭️  Saltando {loc_info.name} (ya existe)')
                    )
                    skipped_count += 1
                    continue
                
                # Datos de ubicación
                location_data = {
                    'name': loc_info.name,
                    'code': code,  # Usar el code del catálogo
                    'address': loc_info.get_mapbox_query(),
                    'city': loc_info.city,
                    'region': loc_info.region,
                    'country': 'Chile',
                }
                
                # Agregar coordenadas si están disponibles
                if loc_info.latitude and loc_info.longitude:
                    location_data['latitude'] = loc_info.latitude
                    location_data['longitude'] = loc_info.longitude
                
                if existing:
                    # Actualizar
                    for key, value in location_data.items():
                        setattr(existing, key, value)
                    existing.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Actualizado: {loc_info.full_name}')
                    )
                    self.stdout.write(f'   📍 {loc_info.address}, {loc_info.city}')
                    updated_count += 1
                else:
                    # Crear nuevo
                    location = Location.objects.create(**location_data)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Creado: {loc_info.full_name}')
                    )
                    self.stdout.write(f'   📍 {loc_info.address}, {loc_info.city}')
                    created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error procesando {loc_info.name}: {e}')
                )
        
        # Resumen
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('  RESUMEN'))
        self.stdout.write('='*70)
        self.stdout.write(f'✅ Ubicaciones creadas: {created_count}')
        self.stdout.write(f'🔄 Ubicaciones actualizadas: {updated_count}')
        self.stdout.write(f'⏭️  Ubicaciones saltadas: {skipped_count}')
        self.stdout.write(f'📍 Total en catálogo: {len(LOCATIONS_CATALOG)}')
        self.stdout.write('='*70 + '\n')
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(self.style.SUCCESS('✅ Ubicaciones cargadas exitosamente\n'))
        else:
            self.stdout.write(self.style.WARNING('ℹ️  No se realizaron cambios\n'))
