#!/usr/bin/env python3
"""
Importador de contenedores desde el archivo de Walmart
"""

import os
import django
import sys
import pandas as pd
from datetime import datetime, date
from django.utils.dateparse import parse_date, parse_datetime

# Configurar Django
sys.path.append('/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container, Agency, ShippingLine, Vessel
from apps.core.models import Company, Location
from decimal import Decimal

def import_walmart_containers():
    """Importa contenedores desde el archivo de Walmart"""
    print("🚀 INICIANDO IMPORTACIÓN DE CONTENEDORES WALMART")
    print("=" * 60)
    
    # Verificar si existe archivo CSV
    file_path = '/workspaces/soptraloc/soptraloc_system/PLANILLA MATRIZ IMPORTACIONES 3(WALMART).csv'
    
    # Si no existe el archivo CSV, usar datos predefinidos
    if not os.path.exists(file_path):
        print("📋 Archivo CSV no encontrado, generando datos de ejemplo...")
        return generate_sample_walmart_data()
    
    # Leer archivo
    df = pd.read_csv(file_path, sep=';', encoding='latin-1')
    
    # Limpiar datos
    df = df.dropna(subset=['Contenedor'])  # Eliminar filas sin contenedor
    df = df[df['Contenedor'] != 'Contenedor']  # Eliminar headers duplicados
    
    print(f"📦 Contenedores a procesar: {len(df)}")
    
    # Obtener o crear empresa Walmart
    walmart, created = Company.objects.get_or_create(
        code='WALMART',
        defaults={
            'name': 'WALMART CHILE S.A.',
            'rut': '12345678-9',
            'email': 'walmart@chile.cl',
            'phone': '+56123456789',
            'address': 'Santiago, Chile'
        }
    )
    
    # Contadores
    imported = 0
    updated = 0
    programmed_count = 0
    
    for idx, row in df.iterrows():
        try:
            container_number = str(row['Contenedor']).strip()
            if not container_number or container_number == 'nan':
                continue
                
            # Obtener o crear contenedor
            container, created = Container.objects.get_or_create(
                container_number=container_number,
                defaults={
                    'owner_company': walmart,
                    'container_type': get_container_type(row.get('Med', '')),
                    'status': map_status(row.get('Status', '')),
                    'position_status': 'floor',
                    'seal_number': str(row.get('Sello', '')),
                    'customs_document': str(row.get('EIR', '')),
                }
            )
            
            if created:
                imported += 1
                print(f"✅ Importado: {container_number} - {container.status}")
            else:
                # Actualizar status si es diferente
                new_status = map_status(row.get('Status', ''))
                if container.status != new_status:
                    container.status = new_status
                    container.save()
                    updated += 1
                    print(f"🔄 Actualizado: {container_number} - {new_status}")
            
            # Contar programados
            if container.status == 'available':
                programmed_count += 1
                
        except Exception as e:
            print(f"❌ Error procesando {row.get('Contenedor', 'Unknown')}: {e}")
    
    print(f"\n📊 RESUMEN DE IMPORTACIÓN:")
    print(f"✅ Contenedores importados: {imported}")
    print(f"🔄 Contenedores actualizados: {updated}")
    print(f"🎯 Contenedores disponibles: {programmed_count}")
    print(f"📦 Total en base de datos: {Container.objects.count()}")

def generate_sample_walmart_data():
    """Genera datos de ejemplo de Walmart cuando no hay CSV"""
    print("🏪 Generando datos de ejemplo de Walmart...")
    
    # Obtener o crear empresa Walmart
    walmart, created = Company.objects.get_or_create(
        code='WALMART',
        defaults={
            'name': 'WALMART CHILE S.A.',
            'rut': '12345678-9',
            'email': 'walmart@chile.cl',
            'phone': '+56123456789',
            'address': 'Santiago, Chile'
        }
    )
    
    # Datos de ejemplo
    sample_containers = [
        {'number': 'WALU1234567', 'type': 'DRY', 'status': 'available'},
        {'number': 'WALU2345678', 'type': 'REEFER', 'status': 'in_transit'},
        {'number': 'WALU3456789', 'type': 'DRY', 'status': 'available'},
        {'number': 'WALU4567890', 'type': 'TANK', 'status': 'loading'},
        {'number': 'WALU5678901', 'type': 'DRY', 'status': 'available'},
    ]
    
    imported = 0
    for container_data in sample_containers:
        container, created = Container.objects.get_or_create(
            container_number=container_data['number'],
            defaults={
                'owner_company': walmart,
                'container_type': container_data['type'],
                'status': container_data['status'],
                'position_status': 'floor',
                'cargo_description': f"Walmart merchandise - {container_data['type']} container",
            }
        )
        
        if created:
            imported += 1
            print(f"✅ Contenedor ejemplo: {container_data['number']}")
    
    print(f"📦 {imported} contenedores de ejemplo creados")

def get_container_type(med_value):
    """Mapea el tipo de contenedor"""
    if not med_value or str(med_value).strip() == 'nan':
        return 'DRY'
        
    med = str(med_value).upper().strip()
    if '40' in med:
        if 'HC' in med:
            return 'FLAT_RACK'
        return 'DRY'
    elif '20' in med:
        return 'DRY'
    elif '45' in med:
        return 'OPEN_TOP'
    return 'DRY'

def map_status(status_value):
    """Mapea el status del contenedor"""
    if not status_value or str(status_value).strip() == 'nan':
        return 'available'
        
    status = str(status_value).upper().strip()
    
    status_mapping = {
        'PROGRAMADO': 'available',
        'FINALIZADO': 'dispatched',
        'LIBERADO': 'dispatched', 
        'DESCARGADO': 'loading',
        'POR ARRIBAR': 'in_transit',
        'EN SECUENCIA': 'loading',
        'TRG': 'available',
    }
    
    return status_mapping.get(status, 'available')

def get_weight(weight_value):
    """Convierte peso a decimal"""
    if not weight_value or str(weight_value).strip() == 'nan':
        return None
        
    try:
        return Decimal(str(weight_value).replace(',', '.'))
    except:
        return None

if __name__ == "__main__":
    import_walmart_containers()