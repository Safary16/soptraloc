#!/usr/bin/env python
"""
Script para actualizar las fechas de programación de contenedores
y añadir datos de destino CD basados en el Excel proporcionado
"""
import os
import django
from datetime import datetime, date, time, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container
from apps.drivers.models import Driver

def update_container_dates():
    """Actualizar fechas de programación para pruebas"""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    print(f"🔄 Actualizando fechas de contenedores...")
    print(f"   Hoy: {today}")
    print(f"   Mañana: {tomorrow}")
    
    # Obtener todos los contenedores
    containers = Container.objects.all()
    
    if not containers.exists():
        print("❌ No hay contenedores en el sistema")
        return
    
    updated_count = 0
    
    # Actualizar contenedores con fechas de hoy y mañana
    for i, container in enumerate(containers[:20]):  # Solo los primeros 20
        # Alternar entre hoy y mañana
        if i % 2 == 0:
            new_date = today
        else:
            new_date = tomorrow
        
        # Asignar horarios variados
        hour = 8 + (i % 12)  # Entre 8:00 y 19:00
        minute = (i * 15) % 60  # Intervalos de 15 minutos
        new_time = time(hour, minute)
        
        # Actualizar el contenedor
        container.scheduled_date = new_date
        container.scheduled_time = new_time
        container.status = 'PROGRAMADO'
        
        # Asignar CD basado en el patrón del Excel
        cd_options = ['CD El Peñón', 'CD Puerto Madero', 'CD Quilicura', 'CD Campos']
        container.cd_location = cd_options[i % len(cd_options)]
        
        # Actualizar posición actual
        if not container.current_position:
            position_options = ['EN_PISO', 'EN_CHASIS', 'CCTI', 'ZEAL', 'CLEP']
            container.current_position = position_options[i % len(position_options)]
        
        container.save()
        updated_count += 1
        
        print(f"✅ {container.container_number}: {new_date} {new_time} -> {container.cd_location}")
    
    print(f"🎉 Actualizados {updated_count} contenedores")

def create_test_drivers():
    """Crear conductores de prueba si no existen"""
    print("🚛 Verificando conductores...")
    
    test_drivers = [
        {
            'nombre': 'Juan Pérez',
            'rut': '12345678-9',
            'ppu': 'ABC123',
            'tipo_conductor': 'LOCALERO',
            'estado': 'OPERATIVO',
            'ubicacion_actual': 'CCTI',
        },
        {
            'nombre': 'Carlos Sánchez',
            'rut': '98765432-1',
            'ppu': 'DEF456',
            'tipo_conductor': 'TRONCO',
            'estado': 'OPERATIVO',
            'ubicacion_actual': 'PUERTO_VALPARAISO',
        },
        {
            'nombre': 'María González',
            'rut': '11111111-1',
            'ppu': 'GHI789',
            'tipo_conductor': 'LOCALERO',
            'estado': 'OPERATIVO',
            'ubicacion_actual': 'CD_PENON',
        },
        {
            'nombre': 'Pedro Martínez',
            'rut': '22222222-2',
            'ppu': 'JKL012',
            'tipo_conductor': 'TRONCO',
            'estado': 'OPERATIVO',
            'ubicacion_actual': 'CD_QUILICURA',
        },
        {
            'nombre': 'Ana Torres',
            'rut': '33333333-3',
            'ppu': 'MNO345',
            'tipo_conductor': 'LOCALERO',
            'estado': 'OPERATIVO',
            'ubicacion_actual': 'CCTI',
        }
    ]
    
    created_count = 0
    for driver_data in test_drivers:
        driver, created = Driver.objects.get_or_create(
            ppu=driver_data['ppu'],
            defaults=driver_data
        )
        if created:
            created_count += 1
            print(f"✅ Creado conductor: {driver.nombre} ({driver.ppu})")
        else:
            # Actualizar estado si ya existe
            driver.estado = 'OPERATIVO'
            driver.contenedor_asignado = None
            driver.save()
            print(f"↻ Actualizado conductor: {driver.nombre} ({driver.ppu})")
    
    print(f"🎉 {created_count} conductores nuevos creados")

if __name__ == '__main__':
    print("🚀 Iniciando actualización del sistema...")
    
    create_test_drivers()
    update_container_dates()
    
    print("✨ Actualización completada!")
    print("\n📋 Resumen:")
    print(f"   • Total contenedores: {Container.objects.count()}")
    print(f"   • Programados hoy: {Container.objects.filter(scheduled_date=date.today()).count()}")
    print(f"   • Programados mañana: {Container.objects.filter(scheduled_date=date.today() + timedelta(days=1)).count()}")
    print(f"   • Total conductores: {Driver.objects.filter(is_active=True).count()}")
    print(f"   • Conductores disponibles: {Driver.objects.filter(estado='OPERATIVO', contenedor_asignado__isnull=True).count()}")