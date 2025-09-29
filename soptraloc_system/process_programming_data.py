#!/usr/bin/env python
"""
Script para procesar datos de programación de contenedores
"""
import os
import sys
import django
from datetime import datetime, timedelta
import pytz

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container

def process_programming_data():
    """Procesar datos de programación específicos"""
    
    # Datos de programación específica
    programming_data = [
        {
            'container': 'IKSU2517896',
            'transportista': 'CCTI',
            'zona': 'Z0',
            'terminal': 'VAL',
            'med': '40',
            'referencia': 'VSCA1421/25',
            'producto': 'WIPES MEDIO',
            'nave': 'RIO DE JANEIRO EXPRE',
            'fecha_programacion': '24/09/2025',
            'wk_demurrage': '40',
            'fecha_demurrage': '01/10/2025',
            'bodega': '6011 - QL SECO',
            'cajas': '1395',
            'hora': '17:00:00'
        },
        {
            'container': 'MORU1320027',
            'transportista': 'CCTI',
            'zona': 'Z0',
            'terminal': 'VAL',
            'med': '40',
            'referencia': 'VSCA1415/25',
            'producto': 'WIPES MEDIO',
            'nave': 'RIO DE JANEIRO EXPRE',
            'fecha_programacion': '24/09/2025',
            'wk_demurrage': '40',
            'fecha_demurrage': '01/10/2025',
            'bodega': '6011 - QL SECO',
            'cajas': '1395',
            'hora': '17:00:00'
        },
        {
            'container': 'ONEU9159010',
            'transportista': 'CCTI',
            'zona': 'Z0',
            'terminal': 'VAL',
            'med': '40',
            'referencia': 'VSCA1422/25',
            'producto': 'WIPES MEDIO',
            'nave': 'RIO DE JANEIRO EXPRE',
            'fecha_programacion': '24/09/2025',
            'wk_demurrage': '40',
            'fecha_demurrage': '01/10/2025',
            'bodega': '6011 - QL SECO',
            'cajas': '1395',
            'hora': '17:00:00'
        },
        {
            'container': 'ONEU9235677',
            'transportista': 'CCTI',
            'zona': 'Z0',
            'terminal': 'VAL',
            'med': '40',
            'referencia': 'VSCA1538/25',
            'producto': 'WIPES MEDIO',
            'nave': 'RIO DE JANEIRO EXPRE',
            'fecha_programacion': '24/09/2025',
            'wk_demurrage': '40',
            'fecha_demurrage': '01/10/2025',
            'bodega': '6011 - QL SECO',
            'cajas': '1395',
            'hora': '17:00:00'
        }
    ]
    
    # Mapeo de bodegas a centros de distribución
    bodega_to_cd = {
        '6011 - QL SECO': 'CD QUILICURA',
        'QL SECO': 'CD QUILICURA',
        'CAMPOS': 'CD CAMPOS DE CHILE',
        'MADERO': 'CD PUERTO MADERO',
        'PEÑON': 'CD EL PEÑÓN'
    }
    
    updated_count = 0
    created_count = 0
    
    print("🚀 PROCESANDO DATOS DE PROGRAMACIÓN")
    print("=" * 50)
    
    for data in programming_data:
        container_number = data['container']
        
        # Buscar contenedor por número
        try:
            container = Container.objects.get(container_number=container_number)
            
            # Parsear fecha de programación
            fecha_prog = datetime.strptime(data['fecha_programacion'], '%d/%m/%Y').date()
            fecha_demurrage = datetime.strptime(data['fecha_demurrage'], '%d/%m/%Y').date()
            
            # Determinar CD basado en bodega
            cd_destino = bodega_to_cd.get(data['bodega'], data['bodega'])
            
            # Actualizar información del contenedor
            container.scheduled_date = fecha_prog
            container.scheduled_time = datetime.strptime(data['hora'], '%H:%M:%S').time()
            container.demurrage_date = fecha_demurrage
            container.cd_location = cd_destino
            container.cargo_description = data['producto']
            container.vessel = data['nave']
            container.terminal = data['terminal']
            container.container_type = f"{data['med']}'"
            container.service_type = data['transportista']
            
            # Asegurar que el contenedor esté PROGRAMADO
            container.status = 'PROGRAMADO'
            
            container.save()
            
            print(f"✅ Actualizado: {container_number} -> {cd_destino} ({fecha_prog})")
            updated_count += 1
            
        except Container.DoesNotExist:
            print(f"❌ Contenedor no encontrado: {container_number}")
            continue
    
    # Programar todos los contenedores PROGRAMADO para hoy y mañana
    hoy = datetime.now().date()
    mañana = hoy + timedelta(days=1)
    
    programados = Container.objects.filter(status='PROGRAMADO')
    
    print(f"\n📅 PROGRAMANDO CONTENEDORES PARA HOY Y MAÑANA")
    print("=" * 50)
    
    for i, container in enumerate(programados):
        # Alternar entre hoy y mañana
        if i % 2 == 0:
            container.scheduled_date = hoy
            fecha_texto = "HOY"
        else:
            container.scheduled_date = mañana
            fecha_texto = "MAÑANA"
            
        # Asignar horarios variados
        horas = ['08:00:00', '09:30:00', '11:00:00', '14:00:00', '15:30:00', '17:00:00']
        hora_asignada = horas[i % len(horas)]
        container.scheduled_time = datetime.strptime(hora_asignada, '%H:%M:%S').time()
        
        container.save()
        print(f"📦 {container.container_number} programado para {fecha_texto} a las {hora_asignada}")
    
    print(f"\n📊 RESUMEN:")
    print(f"✅ Contenedores específicos actualizados: {updated_count}")
    print(f"📅 Total contenedores programados: {programados.count()}")
    print(f"🎯 Listos para asignación de conductores")

if __name__ == "__main__":
    process_programming_data()