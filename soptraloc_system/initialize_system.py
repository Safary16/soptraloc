#!/usr/bin/env python3
"""
Script de inicialización completa del sistema SafaryLoc
Configura el sistema desde cero con todos los datos necesarios
"""

import os
import sys
from pathlib import Path

import django
from datetime import datetime, timedelta, time
import random

# Configurar Django de forma dinámica según la ubicación del script
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management import call_command
from apps.containers.models import Container
from apps.drivers.models import Driver, Location, TimeMatrix
from apps.core.models import Company
from apps.warehouses.models import Warehouse

def initialize_system():
    """Inicializa el sistema completo"""
    print("🚀 INICIALIZACIÓN COMPLETA DEL SISTEMA SAFARYLOC")
    print("=" * 60)
    
    # 1. Crear superusuario si no existe
    create_superuser()
    
    # 2. Verificar ubicaciones (ya existen en el sistema)
    print(f"\n📍 Ubicaciones en sistema: {Location.objects.count()}")
    
    # 3. Verificar matriz de tiempos 
    print(f"⏱️ Matriz de tiempos: {TimeMatrix.objects.count()}")
    
    # 4. Crear empresas
    create_companies()
    
    # 5. Usar comandos existentes para contenedores y conductores
    run_existing_commands()
    
    # 6. Mostrar resumen
    show_summary()
    
    print("\n🎉 ¡SISTEMA COMPLETAMENTE INICIALIZADO!")

def run_existing_commands():
    """Ejecuta los comandos existentes de Django"""
    print("\n📦 Ejecutando comandos de carga de datos...")
    
    try:
        csv_path = Path(__file__).resolve().parent / "PLANILLA MATRIZ IMPORTACIONES 3(WALMART).csv"

        if csv_path.exists():
            print(f"📦 Importando contenedores desde {csv_path.name}...")
            call_command(
                'import_containers',
                str(csv_path),
                '--truncate',
                '--user',
                '1',
            )
            print(f"✅ Contenedores disponibles: {Container.objects.count()}")
        else:
            print(f"⚠️ El archivo de contenedores no existe: {csv_path}")

        try:
            call_command('normalize_container_statuses')
        except Exception as normalize_error:
            print(f"⚠️ No fue posible normalizar estados automáticamente: {normalize_error}")
        
        # Conductores
        from apps.drivers.management.commands.load_drivers import Command as DriverCommand
        driver_cmd = DriverCommand()
        
        current_drivers = Driver.objects.count()
        if current_drivers == 0:
            driver_cmd.handle(count=25)
            print(f"✅ Conductores cargados: {Driver.objects.count()}")
        else:
            print(f"✅ Ya existen {current_drivers} conductores")
            
    except Exception as e:
        print(f"⚠️ Error en comandos automáticos: {e}")
        print("Continuando con datos existentes...")

def create_superuser():
    """Crea el superusuario admin si no existe"""
    print("\n👤 Creando superusuario...")
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@safaryloc.com',
            password='admin123'
        )
        print("✅ Superusuario 'admin' creado (password: admin123)")
    else:
        print("✅ Superusuario ya existe")

def create_base_locations():
    """Crea las ubicaciones base del sistema"""
    print("\n📍 Creando ubicaciones base...")
    
    locations = [
        {'name': 'CCTI - Base Maipú', 'code': 'CCTI', 'address': 'Maipú, Santiago'},
        {'name': 'CD Quilicura', 'code': 'CDQ', 'address': 'Quilicura, Santiago'},
        {'name': 'CD Campos de Chile - Pudahuel', 'code': 'CDC', 'address': 'Pudahuel, Santiago'},
        {'name': 'CD Puerto Madero - Pudahuel', 'code': 'CDM', 'address': 'Pudahuel, Santiago'},
        {'name': 'CD El Peñón - San Bernardo', 'code': 'CDP', 'address': 'San Bernardo, Santiago'},
        {'name': 'Puerto Valparaíso', 'code': 'PVP', 'address': 'Valparaíso'},
        {'name': 'Puerto San Antonio', 'code': 'PSA', 'address': 'San Antonio'},
        {'name': 'Terminal TI', 'code': 'TTI', 'address': 'Santiago'},
        {'name': 'Terminal STI', 'code': 'STI', 'address': 'Santiago'},
        {'name': 'Almacén Extraportuario', 'code': 'AEP', 'address': 'Santiago'},
    ]
    
    created = 0
    for loc_data in locations:
        # Usar name como identificador único principal
        location, created_flag = Location.objects.get_or_create(
            name=loc_data['name'],
            defaults={
                'code': loc_data['code'],
                'address': loc_data['address']
            }
        )
        if created_flag:
            created += 1
    
    print(f"✅ {created} ubicaciones creadas, {Location.objects.count()} total")

def create_time_matrix():
    """Crea la matriz de tiempos entre ubicaciones"""
    print("\n⏱️ Creando matriz de tiempos...")
    
    locations = list(Location.objects.all())
    created = 0
    
    for from_loc in locations:
        for to_loc in locations:
            if from_loc != to_loc:
                # Calcular tiempo estimado basado en distancia simulada
                base_time = random.randint(30, 120)  # Entre 30 y 120 minutos
                loading_time = random.randint(15, 45)  # Entre 15 y 45 minutos
                unloading_time = random.randint(15, 45)  # Entre 15 y 45 minutos
                
                matrix, created_flag = TimeMatrix.objects.get_or_create(
                    from_location=from_loc,
                    to_location=to_loc,
                    defaults={
                        'travel_time': base_time,
                        'loading_time': loading_time,
                        'unloading_time': unloading_time
                    }
                )
                if created_flag:
                    created += 1
    
    print(f"✅ {created} entradas de matriz creadas, {TimeMatrix.objects.count()} total")

def create_companies():
    """Verifica empresas existentes"""
    print("\n🏢 Verificando empresas...")
    
    existing_companies = Company.objects.count()
    print(f"✅ Empresas existentes: {existing_companies}")
    
    if existing_companies == 0:
        print("Creando empresas básicas...")
        try:
            Company.objects.create(name='WALMART SISTEMA', code='WMSYS')
            Company.objects.create(name='SAFARYLOC SISTEMA', code='SFSYS') 
            Company.objects.create(name='PUERTO SISTEMA', code='PTSYS')
            print("✅ Empresas básicas creadas")
        except Exception as e:
            print(f"⚠️ Error creando empresas: {e}")
    
    print(f"✅ Total empresas: {Company.objects.count()}")

def show_summary():
    """Muestra resumen del sistema"""
    print("\n📊 RESUMEN DEL SISTEMA")
    print("-" * 30)
    print(f"👤 Usuarios: {User.objects.count()}")
    print(f"📍 Ubicaciones: {Location.objects.count()}")
    print(f"🏢 Empresas: {Company.objects.count()}")
    print(f"🏭 Almacenes: {Warehouse.objects.count()}")
    print(f"📦 Contenedores: {Container.objects.count()}")
    print(f"🚛 Conductores: {Driver.objects.count()}")
    print(f"⏱️ Matriz de tiempos: {TimeMatrix.objects.count()}")

if __name__ == "__main__":
    initialize_system()

def create_warehouses():
    """Crea almacenes usando el comando existente"""
    print("\n🏪 Creando almacenes...")
    
    try:
        from apps.containers.management.commands.load_walmart_containers import Command as ContainerCommand
        command = ContainerCommand()
        
        # Obtener empresa Walmart
        walmart = Company.objects.get(code='WALMART')
        
        # Crear almacenes
        warehouses = command.create_warehouses(walmart)
        print(f"✅ {len(warehouses)} almacenes Walmart creados")
        
    except Exception as e:
        print(f"⚠️ Error creando almacenes: {e}")
        print("Creando almacenes manualmente...")
        
        # Crear almacén básico si falla el método automático
        from apps.core.models import Location as CoreLocation
        walmart = Company.objects.get(code='WALMART')
        
        location, _ = CoreLocation.objects.get_or_create(
            address='Santiago, Chile',
            defaults={
                'name': 'Walmart Santiago',
                'city': 'Santiago',
                'country': 'Chile'
            }
        )
        
        warehouse, created = Warehouse.objects.get_or_create(
            code='WAL-001',
            defaults={
                'name': 'Walmart Distribution Center Santiago',
                'warehouse_type': 'container_yard',
                'location': location,
                'manager_company': walmart,
                'total_capacity': 150,
                'current_occupancy': 0,
                'operating_hours_start': time(6, 0),
                'operating_hours_end': time(18, 0),
                'operates_weekends': False,
                'contact_phone': '+56223456789',
                'contact_email': 'warehouse@walmart.cl',
                'has_crane': True,
                'has_power': True,
                'has_security': True
            }
        )
        print(f"✅ Almacén básico creado: {warehouse.name}")

def import_containers():
    """Importa contenedores usando el comando existente"""
    print("\n📦 Importando contenedores...")
    
    try:
        from apps.containers.management.commands.load_walmart_containers import Command as ContainerCommand
        
        command = ContainerCommand()
        
        if Container.objects.count() > 0:
            print(f"✅ Ya existen {Container.objects.count()} contenedores")
        else:
            # Ejecutar comando de carga
            command.handle(force=True)
            print(f"✅ Contenedores importados: {Container.objects.count()}")
            
    except Exception as e:
        print(f"⚠️ Error importando contenedores: {e}")
        # Crear algunos contenedores básicos
        create_basic_containers()

def create_basic_containers():
    """Crea contenedores básicos si falla la importación"""
    print("Creando contenedores básicos...")
    
    walmart = Company.objects.get(code='WALMART')
    
    containers_data = [
        {'number': 'WALU1234567', 'type': 'DRY', 'status': 'available'},
        {'number': 'WALU2345678', 'type': 'REEFER', 'status': 'in_transit'},
        {'number': 'WALU3456789', 'type': 'DRY', 'status': 'available'},
        {'number': 'WALU4567890', 'type': 'TANK', 'status': 'loading'},
        {'number': 'WALU5678901', 'type': 'DRY', 'status': 'available'},
    ]
    
    created = 0
    for container_data in containers_data:
        container, created_flag = Container.objects.get_or_create(
            container_number=container_data['number'],
            defaults={
                'owner_company': walmart,
                'container_type': container_data['type'],
                'status': container_data['status'],
                'position_status': 'floor',
                'cargo_description': f"Walmart merchandise - {container_data['type']} container",
            }
        )
        if created_flag:
            created += 1
    
    print(f"✅ {created} contenedores básicos creados")

def create_drivers():
    """Crea conductores usando el comando existente"""
    print("\n🚗 Creando conductores...")
    
    try:
        from apps.drivers.management.commands.load_drivers import Command as DriverCommand
        
        command = DriverCommand()
        
        if Driver.objects.count() > 0:
            print(f"✅ Ya existen {Driver.objects.count()} conductores")
        else:
            # Ejecutar comando de carga
            command.handle(count=25, force=True)
            print(f"✅ Conductores creados: {Driver.objects.count()}")
            
    except Exception as e:
        print(f"⚠️ Error creando conductores: {e}")
        # Crear algunos conductores básicos
        create_basic_drivers()

def create_basic_drivers():
    """Crea conductores básicos si falla la creación automática"""
    print("Creando conductores básicos...")
    
    drivers_data = [
        {'nombre': 'Juan Pérez', 'rut': '12345678-9', 'ppu': 'AB1234', 'estado': 'OPERATIVO'},
        {'nombre': 'María González', 'rut': '23456789-0', 'ppu': 'CD5678', 'estado': 'OPERATIVO'},
        {'nombre': 'Carlos Silva', 'rut': '34567890-1', 'ppu': 'EF9012', 'estado': 'OPERATIVO'},
        {'nombre': 'Ana López', 'rut': '45678901-2', 'ppu': 'GH3456', 'estado': 'OPERATIVO'},
        {'nombre': 'Pedro Martínez', 'rut': '56789012-3', 'ppu': 'IJ7890', 'estado': 'OPERATIVO'},
    ]
    
    created = 0
    for driver_data in drivers_data:
        driver, created_flag = Driver.objects.get_or_create(
            rut=driver_data['rut'],
            defaults={
                'nombre': driver_data['nombre'],
                'ppu': driver_data['ppu'],
                'tipo_conductor': 'LOCALERO',
                'estado': driver_data['estado'],
                'ubicacion_actual': 'CCTI',
                'telefono': '+56987654321'
            }
        )
        if created_flag:
            created += 1
    
    print(f"✅ {created} conductores básicos creados")

def show_summary():
    """Muestra resumen del sistema inicializado"""
    print("\n📊 RESUMEN DEL SISTEMA INICIALIZADO")
    print("=" * 50)
    
    print(f"👤 Usuarios: {User.objects.count()}")
    print(f"🏢 Empresas: {Company.objects.count()}")
    print(f"📍 Ubicaciones: {Location.objects.count()}")
    print(f"⏱️ Matriz de tiempos: {TimeMatrix.objects.count()}")
    print(f"🏪 Almacenes: {Warehouse.objects.count()}")
    print(f"📦 Contenedores: {Container.objects.count()}")
    print(f"🚗 Conductores: {Driver.objects.count()}")
    
    # Mostrar conductores operativos
    operativos = Driver.objects.filter(estado='OPERATIVO').count()
    print(f"🟢 Conductores operativos: {operativos}")
    
    # Mostrar contenedores disponibles
    disponibles = Container.objects.filter(status='available').count()
    print(f"📦 Contenedores disponibles: {disponibles}")

if __name__ == "__main__":
    initialize_system()