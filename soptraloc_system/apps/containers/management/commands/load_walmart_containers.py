"""
Comando para cargar automáticamente los 692 contenedores de Walmart
Se ejecuta automáticamente en el deploy de Render
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.containers.models import Container
from apps.warehouses.models import Warehouse
from apps.core.models import Location, Company
from datetime import datetime, timedelta, time
import random


class Command(BaseCommand):
    help = 'Carga automáticamente los 692 contenedores de Walmart con datos realistas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recarga incluso si ya existen contenedores',
        )

    def handle(self, *args, **options):
        # Verificar si ya existen contenedores
        if Container.objects.count() > 0 and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Ya existen {Container.objects.count()} contenedores en el sistema')
            )
            return

        self.stdout.write('🚀 Iniciando carga de contenedores de Walmart...')

        # Crear datos base
        company = self.create_company()
        warehouses = self.create_warehouses(company)
        locations = self.create_locations(warehouses)
        
        # Generar y crear contenedores
        containers_created = self.create_containers(warehouses, locations)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ ¡Completado! Se crearon {containers_created} contenedores de Walmart'
            )
        )

    def create_company(self):
        """Crear compañía Walmart"""
        company, created = Company.objects.get_or_create(
            code="WAL-CORP",
            defaults={
                'name': "Walmart Inc.",
                'rut': "12345678-9",
                'email': 'operations@walmart.com',
                'phone': '+1-800-WALMART',
                'address': '702 SW 8th Street, Bentonville, AR 72716, USA'
            }
        )
        return company

    def create_warehouses(self, company):
        """Crear almacenes de Walmart"""
        warehouses_data = [
            ('WAL-001', 'Walmart DC Miami', 'Miami, FL', 'container_yard'),
            ('WAL-002', 'Walmart DC Los Angeles', 'Los Angeles, CA', 'container_yard'),
            ('WAL-003', 'Walmart Hub New York', 'New York, NY', 'covered'),
            ('WAL-004', 'Walmart Center Houston', 'Houston, TX', 'container_yard'),
            ('WAL-005', 'Walmart DC Chicago', 'Chicago, IL', 'covered'),
        ]
        
        warehouses = []
        for code, name, location_name, warehouse_type in warehouses_data:
            # Crear ubicación del almacén
            location, created = Location.objects.get_or_create(
                address=location_name,
                defaults={
                    'name': f'Location {name}',
                    'city': location_name.split(', ')[0],
                    'country': 'United States'
                }
            )
            
            # Crear almacén
            warehouse, created = Warehouse.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'warehouse_type': warehouse_type,
                    'location': location,
                    'manager_company': company,
                    'total_capacity': random.randint(150, 200),
                    'current_occupancy': 0,
                    'operating_hours_start': time(6, 0),
                    'operating_hours_end': time(18, 0),
                    'operates_weekends': False,
                    'contact_phone': '+1-305-555-0100',
                    'contact_email': f'warehouse.{code.lower()}@walmart.com',
                    'has_crane': True,
                    'has_power': True,
                    'has_security': True
                }
            )
            warehouses.append(warehouse)
            
        return warehouses

    def create_locations(self, warehouses):
        """Crear ubicaciones para contenedores"""
        locations = []
        
        for warehouse in warehouses:
            # Crear ubicaciones de piso
            for floor in range(1, 6):  # Pisos 1-5
                for spot in range(1, 21):  # Espacios 1-20
                    location, created = Location.objects.get_or_create(
                        name=f"Floor-{floor}-{spot}",
                        defaults={
                            'address': f'{warehouse.name} - Floor {floor} Spot {spot}',
                            'city': warehouse.location.city,
                            'country': warehouse.location.country
                        }
                    )
                    locations.append(location)
            
            # Crear ubicaciones de chasis
            for chassis in range(100, 200):  # Chasis 100-199
                location, created = Location.objects.get_or_create(
                    name=f"Chassis-{chassis}",
                    defaults={
                        'address': f'{warehouse.name} - Chassis {chassis}',
                        'city': warehouse.location.city,
                        'country': warehouse.location.country
                    }
                )
                locations.append(location)
                
        return locations

    def create_containers(self, warehouses, locations):
        """Crear contenedores usando solo campos que existen en el modelo"""
        container_types = ['DRY', 'REEFER', 'TANK', 'FLAT_RACK', 'OPEN_TOP']
        statuses = ['available', 'in_transit', 'loading', 'dispatched']
        position_statuses = ['floor', 'chassis', 'truck', 'yard']
        
        containers_created = 0
        base_date = datetime.now().date()
        
        # Conseguir una compañía para usar como owner
        company = Company.objects.first()
        if not company:
            company = Company.objects.create(
                name="Default Company",
                code="DEFAULT",
                rut="99999999-9",
                email="default@company.com",
                phone="+1-000-000-0000",
                address="Default Address"
            )
        
        with transaction.atomic():
            for i in range(692):
                # Datos básicos que sabemos que existen
                container_number = f"WAL{random.randint(100000, 999999)}"
                container_type = random.choice(container_types)
                status = random.choice(statuses)
                position_status = random.choice(position_statuses)
                current_location = random.choice(locations)
                
                # Fechas
                eta_days = random.randint(0, 30)
                eta_date = base_date + timedelta(days=eta_days)
                
                # Crear contenedor con solo campos que sabemos que existen
                container = Container.objects.create(
                    container_number=container_number,
                    container_type=container_type,
                    status=status,
                    position_status=position_status,
                    owner_company=company,
                    current_location=current_location,
                    eta=eta_date,
                    cargo_description=f"Walmart merchandise - Container {container_number}",
                    special_requirements="Handle with care"
                )
                
                containers_created += 1
                
                if containers_created % 50 == 0:
                    self.stdout.write(f'📦 Creados {containers_created} contenedores...')

        return containers_created