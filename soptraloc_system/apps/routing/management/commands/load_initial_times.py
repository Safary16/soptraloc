"""
Carga tiempos iniciales para ubicaciones comunes en Chile.
Basado en tiempos típicos de Santiago y Valparaíso.

Uso:
    python manage.py load_initial_times
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.drivers.models import Location
from apps.routing.models import LocationPair, OperationTime


class Command(BaseCommand):
    help = 'Carga tiempos iniciales de rutas y operaciones comunes en Chile'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Eliminar tiempos existentes antes de cargar'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write(self.style.HTTP_INFO('⏱️  CARGA DE TIEMPOS INICIALES'))
        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write('')
        
        if options['reset']:
            self.stdout.write('🗑️  Eliminando datos existentes...')
            LocationPair.objects.all().delete()
            OperationTime.objects.all().delete()
            self.stdout.write(self.style.WARNING('   Datos eliminados'))
            self.stdout.write('')
        
        # Crear/obtener ubicaciones
        locations = self._create_locations()
        
        # Crear pares de ubicaciones
        self._create_location_pairs(locations)
        
        # Crear tiempos de operaciones
        self._create_operation_times(locations)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('✅ CARGA COMPLETADA'))
        self.stdout.write(self.style.SUCCESS('='*60))
    
    def _create_locations(self):
        """Crea o obtiene ubicaciones comunes."""
        self.stdout.write('📍 Creando ubicaciones...')
        
        locations_data = [
            # Base y centros de distribución
            ('CCTI - Base Maipú', '-33.5083', '-70.7625'),
            ('CD Quilicura', '-33.3606', '-70.7394'),
            ('CD Campos de Chile - Pudahuel', '-33.3911', '-70.7631'),
            ('CD Puerto Madero - Pudahuel', '-33.3850', '-70.7700'),
            ('CD El Peñón - San Bernardo', '-33.6281', '-70.7008'),
            
            # Puertos
            ('Puerto Valparaíso', '-33.0340', '-71.6275'),
            ('Puerto San Antonio', '-33.5928', '-71.6105'),
            ('TPS Valparaíso', '-33.0320', '-71.6290'),
            ('TCVAL Valparaíso', '-33.0360', '-71.6260'),
            ('STI San Antonio', '-33.5935', '-71.6110'),
            
            # Almacenes extraportuarios
            ('Almacén Extraportuario Valparaíso', '-33.0500', '-71.6200'),
            ('Almacén Extraportuario San Antonio', '-33.6000', '-71.6000'),
        ]
        
        locations = {}
        for name, lat, lon in locations_data:
            # Buscar por nombre (único en el contexto)
            location, created = Location.objects.get_or_create(
                name=name,
                defaults={
                    'latitude': lat,
                    'longitude': lon,
                    'address': name,
                    'is_active': True
                }
            )
            locations[name] = location
            
            if created:
                self.stdout.write(f'  ✅ Creada: {name}')
            else:
                self.stdout.write(f'  ℹ️  Existente: {name}')
        
        self.stdout.write('')
        return locations
    
    def _create_location_pairs(self, locations):
        """Crea pares de ubicaciones con tiempos."""
        self.stdout.write('🚛 Creando tiempos de trayectos...')
        
        # Formato: (origen, destino, tiempo_base_min, tipo, distancia_km)
        pairs_data = [
            # Desde puertos a almacenes extraportuarios
            ('Puerto Valparaíso', 'Almacén Extraportuario Valparaíso', 25, 'PORT_ACCESS', 5),
            ('Puerto San Antonio', 'Almacén Extraportuario San Antonio', 20, 'PORT_ACCESS', 3),
            
            # Desde almacenes extraportuarios a CCTI/CDs
            ('Almacén Extraportuario Valparaíso', 'CCTI - Base Maipú', 90, 'HIGHWAY', 110),
            ('Almacén Extraportuario Valparaíso', 'CD Quilicura', 100, 'HIGHWAY', 120),
            ('Almacén Extraportuario Valparaíso', 'CD Campos de Chile - Pudahuel', 95, 'HIGHWAY', 115),
            ('Almacén Extraportuario Valparaíso', 'CD Puerto Madero - Pudahuel', 95, 'HIGHWAY', 115),
            ('Almacén Extraportuario Valparaíso', 'CD El Peñón - San Bernardo', 100, 'HIGHWAY', 125),
            
            ('Almacén Extraportuario San Antonio', 'CCTI - Base Maipú', 110, 'HIGHWAY', 130),
            ('Almacén Extraportuario San Antonio', 'CD Quilicura', 120, 'HIGHWAY', 140),
            ('Almacén Extraportuario San Antonio', 'CD Campos de Chile - Pudahuel', 115, 'HIGHWAY', 135),
            ('Almacén Extraportuario San Antonio', 'CD Puerto Madero - Pudahuel', 115, 'HIGHWAY', 135),
            ('Almacén Extraportuario San Antonio', 'CD El Peñón - San Bernardo', 105, 'HIGHWAY', 120),
            
            # Desde puertos directo a CCTI/CDs
            ('Puerto Valparaíso', 'CCTI - Base Maipú', 105, 'HIGHWAY', 115),
            ('Puerto Valparaíso', 'CD Quilicura', 115, 'HIGHWAY', 125),
            ('Puerto Valparaíso', 'CD Campos de Chile - Pudahuel', 110, 'HIGHWAY', 120),
            ('Puerto Valparaíso', 'CD Puerto Madero - Pudahuel', 110, 'HIGHWAY', 120),
            ('Puerto Valparaíso', 'CD El Peñón - San Bernardo', 115, 'HIGHWAY', 130),
            
            ('Puerto San Antonio', 'CCTI - Base Maipú', 120, 'HIGHWAY', 135),
            ('Puerto San Antonio', 'CD Quilicura', 130, 'HIGHWAY', 145),
            ('Puerto San Antonio', 'CD Campos de Chile - Pudahuel', 125, 'HIGHWAY', 140),
            ('Puerto San Antonio', 'CD Puerto Madero - Pudahuel', 125, 'HIGHWAY', 140),
            ('Puerto San Antonio', 'CD El Peñón - San Bernardo', 115, 'HIGHWAY', 125),
            
            # Entre CDs (Santiago)
            ('CCTI - Base Maipú', 'CD Quilicura', 35, 'URBAN', 25),
            ('CCTI - Base Maipú', 'CD Campos de Chile - Pudahuel', 30, 'URBAN', 20),
            ('CCTI - Base Maipú', 'CD Puerto Madero - Pudahuel', 32, 'URBAN', 22),
            ('CCTI - Base Maipú', 'CD El Peñón - San Bernardo', 40, 'URBAN', 28),
            
            ('CD Quilicura', 'CD Campos de Chile - Pudahuel', 20, 'URBAN', 12),
            ('CD Quilicura', 'CD Puerto Madero - Pudahuel', 22, 'URBAN', 14),
            ('CD Quilicura', 'CD El Peñón - San Bernardo', 45, 'URBAN', 32),
            
            ('CD Campos de Chile - Pudahuel', 'CD Puerto Madero - Pudahuel', 15, 'URBAN', 8),
            ('CD Campos de Chile - Pudahuel', 'CD El Peñón - San Bernardo', 40, 'URBAN', 28),
            
            ('CD Puerto Madero - Pudahuel', 'CD El Peñón - San Bernardo', 42, 'URBAN', 30),
            
            # Terminales Valparaíso
            ('TPS Valparaíso', 'CCTI - Base Maipú', 105, 'HIGHWAY', 115),
            ('TCVAL Valparaíso', 'CCTI - Base Maipú', 105, 'HIGHWAY', 115),
            
            # Terminal San Antonio
            ('STI San Antonio', 'CCTI - Base Maipú', 120, 'HIGHWAY', 135),
        ]
        
        created_count = 0
        for origin_name, dest_name, time, route_type, distance in pairs_data:
            if origin_name not in locations or dest_name not in locations:
                continue
            
            pair, created = LocationPair.objects.get_or_create(
                origin=locations[origin_name],
                destination=locations[dest_name],
                defaults={
                    'base_travel_time': time,
                    'route_type': route_type,
                    'distance_km': distance,
                    'peak_hour_multiplier': 1.3 if route_type == 'URBAN' else 1.15,
                    'peak_hours_start': '08:00',
                    'peak_hours_end': '10:00',
                    'peak_hours_2_start': '18:00',
                    'peak_hours_2_end': '20:00',
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                origin_short = origin_name.split(' - ')[0]
                dest_short = dest_name.split(' - ')[0]
                self.stdout.write(
                    f'  ✅ {origin_short} → {dest_short}: {time} min ({distance} km)'
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'  Total creados: {created_count} pares'))
        self.stdout.write('')
    
    def _create_operation_times(self, locations):
        """Crea tiempos de operaciones en ubicaciones."""
        self.stdout.write('⚙️  Creando tiempos de operaciones...')
        
        # Operaciones en CCTI (base)
        ccti_operations = [
            ('CHASSIS_HOOK', 10, 15, 20),
            ('CHASSIS_UNHOOK', 8, 12, 15),
            ('CONTAINER_TO_FLOOR', 12, 18, 25),
            ('CONTAINER_FROM_FLOOR', 12, 18, 25),
            ('WAREHOUSE_CHECKIN', 5, 10, 15),
            ('WAREHOUSE_CHECKOUT', 5, 10, 15),
            ('PAPERWORK', 10, 20, 30),
            ('INSPECTION', 15, 25, 40),
        ]
        
        # Operaciones en CDs (clientes)
        cd_operations = [
            ('CLIENT_DELIVERY', 20, 30, 45),
            ('CLIENT_PICKUP', 15, 25, 35),
            ('CONTAINER_UNLOAD', 15, 25, 40),
            ('WAITING', 10, 20, 60),
            ('PAPERWORK', 5, 15, 25),
        ]
        
        # Operaciones portuarias
        port_operations = [
            ('PORT_GATE_IN', 15, 25, 45),
            ('PORT_GATE_OUT', 10, 20, 40),
            ('PORT_PICKUP', 20, 35, 60),
            ('PORT_DELIVERY', 20, 35, 60),
            ('PAPERWORK', 15, 30, 60),
            ('INSPECTION', 20, 40, 90),
        ]
        
        # Operaciones en almacenes extraportuarios
        warehouse_operations = [
            ('WAREHOUSE_STORAGE', 15, 25, 40),
            ('WAREHOUSE_CHECKIN', 10, 20, 35),
            ('WAREHOUSE_CHECKOUT', 10, 20, 35),
            ('CONTAINER_TO_FLOOR', 12, 18, 25),
            ('CONTAINER_FROM_FLOOR', 12, 18, 25),
            ('PAPERWORK', 10, 20, 30),
        ]
        
        created_count = 0
        
        # CCTI
        if 'CCTI - Base Maipú' in locations:
            for op_type, min_t, avg_t, max_t in ccti_operations:
                _, created = OperationTime.objects.get_or_create(
                    location=locations['CCTI - Base Maipú'],
                    operation_type=op_type,
                    defaults={
                        'min_time': min_t,
                        'avg_time': avg_t,
                        'max_time': max_t,
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1
        
        # CDs
        cd_names = [
            'CD Quilicura',
            'CD Campos de Chile - Pudahuel',
            'CD Puerto Madero - Pudahuel',
            'CD El Peñón - San Bernardo'
        ]
        for cd_name in cd_names:
            if cd_name in locations:
                for op_type, min_t, avg_t, max_t in cd_operations:
                    _, created = OperationTime.objects.get_or_create(
                        location=locations[cd_name],
                        operation_type=op_type,
                        defaults={
                            'min_time': min_t,
                            'avg_time': avg_t,
                            'max_time': max_t,
                            'depends_on_container_size': True,
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
        
        # Puertos
        port_names = [
            'Puerto Valparaíso',
            'Puerto San Antonio',
            'TPS Valparaíso',
            'TCVAL Valparaíso',
            'STI San Antonio'
        ]
        for port_name in port_names:
            if port_name in locations:
                for op_type, min_t, avg_t, max_t in port_operations:
                    _, created = OperationTime.objects.get_or_create(
                        location=locations[port_name],
                        operation_type=op_type,
                        defaults={
                            'min_time': min_t,
                            'avg_time': avg_t,
                            'max_time': max_t,
                            'depends_on_time_of_day': True,
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
        
        # Almacenes extraportuarios
        warehouse_names = [
            'Almacén Extraportuario Valparaíso',
            'Almacén Extraportuario San Antonio'
        ]
        for warehouse_name in warehouse_names:
            if warehouse_name in locations:
                for op_type, min_t, avg_t, max_t in warehouse_operations:
                    _, created = OperationTime.objects.get_or_create(
                        location=locations[warehouse_name],
                        operation_type=op_type,
                        defaults={
                            'min_time': min_t,
                            'avg_time': avg_t,
                            'max_time': max_t,
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  Total creados: {created_count} operaciones'))
