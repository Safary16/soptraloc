from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.core.models import Company, Vehicle, MovementCode
from apps.drivers.models import Driver, Location


class Command(BaseCommand):
    help = 'Carga datos de ejemplo para SOPTRALOC'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Creando datos de ejemplo para SOPTRALOC...")
        
        # Crear empresas
        self.stdout.write("📋 Creando empresas...")
        companies = [
            {
                'name': 'Transportes Martínez S.A.',
                'code': 'TRMZ',
                'rut': '76.123.456-7',
                'email': 'contacto@transportesmartinez.cl',
                'phone': '+56912345678',
                'address': 'Av. Providencia 1234, Santiago, Chile'
            },
            {
                'name': 'Logística del Pacífico Ltda.',
                'code': 'LPAC',
                'rut': '88.987.654-3',
                'email': 'info@logisticapacifico.cl',
                'phone': '+56987654321',
                'address': 'Camino al Aeropuerto 5678, Santiago, Chile'
            },
            {
                'name': 'Contenedores del Sur SpA',
                'code': 'CSUR',
                'rut': '99.555.444-1',
                'email': 'ventas@contenedoresdelsur.cl',
                'phone': '+56955544433',
                'address': 'Ruta 5 Sur Km 120, Rancagua, Chile'
            }
        ]
        
        for company_data in companies:
            company, created = Company.objects.get_or_create(
                code=company_data['code'],
                defaults=company_data
            )
            if created:
                self.stdout.write(f"  ✅ Empresa creada: {company.name}")
            else:
                self.stdout.write(f"  ⚠️ Empresa ya existe: {company.name}")
        
        # Crear ubicaciones
        self.stdout.write("📍 Creando ubicaciones...")
        locations = [
            {
                'name': 'Terminal San Antonio',
                'address': 'Puerto San Antonio, V Región',
                'city': 'San Antonio',
                'region': 'Valparaíso',
                'latitude': -33.5918,
                'longitude': -71.6127
            },
            {
                'name': 'Terminal Valparaíso',
                'address': 'Puerto de Valparaíso, V Región',
                'city': 'Valparaíso',
                'region': 'Valparaíso',
                'latitude': -33.0472,
                'longitude': -71.6127
            },
            {
                'name': 'Depósito Santiago Norte',
                'address': 'Av. Américo Vespucio 1500, Quilicura',
                'city': 'Santiago',
                'region': 'Metropolitana',
                'latitude': -33.3644,
                'longitude': -70.7394
            },
            {
                'name': 'Centro Logístico Melipilla',
                'address': 'Ruta 78 Km 47, Melipilla',
                'city': 'Melipilla',
                'region': 'Metropolitana',
                'latitude': -33.6969,
                'longitude': -71.2158
            }
        ]
        
        for location_data in locations:
            location, created = Location.objects.get_or_create(
                name=location_data['name'],
                defaults=location_data
            )
            if created:
                self.stdout.write(f"  ✅ Ubicación creada: {location.name}")
            else:
                self.stdout.write(f"  ⚠️ Ubicación ya existe: {location.name}")
        
        # Crear usuarios para conductores
        self.stdout.write("👥 Creando usuarios y conductores...")
        drivers_data = [
            {
                'first_name': 'Juan Carlos',
                'last_name': 'González',
                'username': 'jc.gonzalez',
                'email': 'jc.gonzalez@soptraloc.local',
                'license_number': 'A1-12345678',
                'phone': '+56911111111'
            },
            {
                'first_name': 'María Elena',
                'last_name': 'Rodríguez',
                'username': 'm.rodriguez',
                'email': 'm.rodriguez@soptraloc.local',
                'license_number': 'A1-87654321',
                'phone': '+56922222222'
            },
            {
                'first_name': 'Pedro Antonio',
                'last_name': 'Silva',
                'username': 'p.silva',
                'email': 'p.silva@soptraloc.local',
                'license_number': 'A1-55555555',
                'phone': '+56933333333'
            },
            {
                'first_name': 'Ana María',
                'last_name': 'Torres',
                'username': 'a.torres',
                'email': 'a.torres@soptraloc.local',
                'license_number': 'A1-99999999',
                'phone': '+56944444444'
            }
        ]
        
        for driver_data in drivers_data:
            user, created = User.objects.get_or_create(
                username=driver_data['username'],
                defaults={
                    'first_name': driver_data['first_name'],
                    'last_name': driver_data['last_name'],
                    'email': driver_data['email'],
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('conductor123')
                user.save()
                self.stdout.write(f"  ✅ Usuario creado: {user.username}")
            else:
                self.stdout.write(f"  ⚠️ Usuario ya existe: {user.username}")
            
            driver, created = Driver.objects.get_or_create(
                user=user,
                defaults={
                    'license_number': driver_data['license_number'],
                    'phone': driver_data['phone'],
                    'is_available': True
                }
            )
            
            if created:
                self.stdout.write(f"  ✅ Conductor creado: {driver.user.get_full_name()}")
            else:
                self.stdout.write(f"  ⚠️ Conductor ya existe: {driver.user.get_full_name()}")
        
        # Crear vehículos
        self.stdout.write("🚛 Creando vehículos...")
        vehicles = [
            {
                'plate': 'ABCD12',
                'vehicle_type': 'truck',
                'brand': 'Volvo',
                'model': 'FH16',
                'year': 2020,
                'status': 'available',
                'max_capacity': 40.0
            },
            {
                'plate': 'EFGH34',
                'vehicle_type': 'chassis',
                'brand': 'Mercedes-Benz',
                'model': 'Actros',
                'year': 2019,
                'status': 'available',
                'max_capacity': 35.0
            },
            {
                'plate': 'IJKL56',
                'vehicle_type': 'truck',
                'brand': 'Scania',
                'model': 'R450',
                'year': 2021,
                'status': 'in_use',
                'max_capacity': 42.0
            },
            {
                'plate': 'MNOP78',
                'vehicle_type': 'chassis',
                'brand': 'DAF',
                'model': 'XF',
                'year': 2018,
                'status': 'maintenance',
                'max_capacity': 38.0
            },
            {
                'plate': 'QRST90',
                'vehicle_type': 'trailer',
                'brand': 'Krone',
                'model': 'Profi Liner',
                'year': 2020,
                'status': 'available',
                'max_capacity': 30.0
            }
        ]
        
        for vehicle_data in vehicles:
            vehicle, created = Vehicle.objects.get_or_create(
                plate=vehicle_data['plate'],
                defaults=vehicle_data
            )
            if created:
                self.stdout.write(f"  ✅ Vehículo creado: {vehicle.plate} - {vehicle.get_vehicle_type_display()}")
            else:
                self.stdout.write(f"  ⚠️ Vehículo ya existe: {vehicle.plate}")
        
        # Crear algunos códigos de movimiento de ejemplo
        self.stdout.write("🔢 Creando códigos de movimiento...")
        movement_types = ['load', 'unload', 'transfer']
        for movement_type in movement_types:
            for i in range(3):  # 3 códigos por tipo
                code = MovementCode.generate_code(movement_type)
                self.stdout.write(f"  ✅ Código generado: {code.code} ({movement_type})")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 ¡Datos de ejemplo creados exitosamente!"))
        self.stdout.write("\n📊 Resumen:")
        self.stdout.write(f"  • Empresas: {Company.objects.count()}")
        self.stdout.write(f"  • Conductores: {Driver.objects.count()}")
        self.stdout.write(f"  • Vehículos: {Vehicle.objects.count()}")
        self.stdout.write(f"  • Ubicaciones: {Location.objects.count()}")
        self.stdout.write(f"  • Códigos de movimiento: {MovementCode.objects.count()}")
        
        self.stdout.write("\n🌐 URLs importantes:")
        self.stdout.write("  • Panel Admin: http://localhost:8000/admin/")
        self.stdout.write("  • API Dashboard: http://localhost:8000/api/v1/core/dashboard/")
        self.stdout.write("  • Documentación API: http://localhost:8000/swagger/")
        self.stdout.write("\n💡 Usuario admin: admin (contraseña configurada al crear superuser)")
        self.stdout.write("💡 Conductores: contraseña 'conductor123'")