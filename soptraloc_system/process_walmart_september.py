#!/usr/bin/env python3
"""
Procesador optimizado de datos de Walmart - Solo septiembre
Enfoque específico en datos reales de Walmart del archivo CSV
"""

import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, date, time
import unicodedata

# Configurar Django
sys.path.append('/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container, Agency, ShippingLine
from apps.core.models import Company

def normalize_text(text):
    """Normalizar texto removiendo acentos y espacios extra"""
    if pd.isna(text) or text is None:
        return ''
    text = str(text)
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in normalized if not unicodedata.combining(c)]).strip()

def process_walmart_september_data():
    """Procesar específicamente datos de Walmart del CSV de septiembre"""
    
    print("🏪 PROCESANDO DATOS WALMART - SEPTIEMBRE 2025")
    print("=" * 60)
    
    # Buscar archivo CSV
    csv_files = ['9 (1).csv', '9.csv', 'septiembre.csv']
    csv_file = None
    
    for filename in csv_files:
        if os.path.exists(filename):
            csv_file = filename
            break
    
    if not csv_file:
        print("❌ No se encuentra archivo CSV de septiembre")
        return False
    
    print(f"📄 Archivo encontrado: {csv_file}")
    
    # Leer CSV con múltiples intentos
    df = None
    for sep in [';', ',', '\t']:
        for encoding in ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']:
            try:
                temp_df = pd.read_csv(csv_file, sep=sep, encoding=encoding)
                if len(temp_df.columns) > 5:  # Verificar columnas suficientes
                    df = temp_df
                    print(f"✅ CSV leído: separador '{sep}', encoding '{encoding}'")
                    print(f"📊 Registros totales: {len(df)}")
                    print(f"📋 Columnas: {len(df.columns)}")
                    break
            except:
                continue
        if df is not None:
            break
    
    if df is None:
        print("❌ No se pudo leer el archivo CSV")
        return False
    
    # Mostrar primeras columnas para mapeo
    print(f"\n📋 Primeras 10 columnas:")
    for i, col in enumerate(df.columns[:10]):
        print(f"  {i+1}. {col}")
    
    # Filtrar datos de Walmart
    walmart_keywords = [
        'WALMART', 'walmart', 'Walmart', 
        'LIDER', 'lider', 'Lider',
        'CENTRAL', 'central'
    ]
    
    # Buscar en todas las columnas de texto
    walmart_mask = pd.Series([False] * len(df))
    text_cols = df.select_dtypes(include=['object']).columns
    
    for col in text_cols:
        col_data = df[col].astype(str).str.upper()
        for keyword in walmart_keywords:
            walmart_mask |= col_data.str.contains(keyword.upper(), na=False)
    
    walmart_df = df[walmart_mask].copy()
    print(f"\n🎯 Registros de Walmart: {len(walmart_df)}")
    
    if len(walmart_df) == 0:
        print("⚠️ No se encontraron registros específicos de Walmart")
        # Usar una muestra si no hay filtro específico
        walmart_df = df.head(50).copy()
        print(f"📦 Procesando muestra: {len(walmart_df)} registros")
    
    # Crear/obtener empresa Walmart
    walmart_company, created = Company.objects.get_or_create(
        code='WALMART',
        defaults={
            'name': 'Walmart Chile S.A.',
            'rut': '76.833.300-8',
            'email': 'logistica@walmart.cl',
            'phone': '+56 2 2000 0000',
            'address': 'Santiago, Chile'
        }
    )
    
    if created:
        print("✅ Empresa Walmart creada en BD")
    else:
        print("✅ Empresa Walmart ya existe")
    
    # Mapeo inteligente de columnas
    column_patterns = {
        'container': r'(contenedor|container|numero|number|equipo)',
        'client': r'(client|cliente|empresa|company|consign|destinatario)',
        'destination': r'(destino|destination|cd|centro|ubicacion)',
        'date': r'(fecha|date|programacion|scheduled|arribo)',
        'time': r'(hora|time|horario)',
        'driver': r'(conductor|driver|chofer)',
        'vehicle': r'(ppu|patente|plate|vehiculo|tracto)',
        'status': r'(estado|status|situacion)'
    }
    
    # Encontrar columnas relevantes
    mapped_columns = {}
    for field, pattern in column_patterns.items():
        for col in df.columns:
            col_clean = normalize_text(col).upper()
            import re
            if re.search(pattern, col_clean, re.IGNORECASE):
                mapped_columns[field] = col
                print(f"📌 {field}: {col}")
                break
    
    # Procesar registros de Walmart
    containers_processed = 0
    containers_created = 0
    containers_updated = 0
    
    print(f"\n🔄 Procesando {len(walmart_df)} registros...")
    
    for idx, row in walmart_df.iterrows():
        try:
            # Extraer número de contenedor
            container_number = None
            
            if 'container' in mapped_columns:
                container_number = normalize_text(str(row[mapped_columns['container']]))
            
            # Si no encontramos, buscar patrón en todas las columnas
            if not container_number or len(container_number) < 4:
                for col in df.columns:
                    val = normalize_text(str(row[col]))
                    # Patrón típico de contenedor: 4 letras + 6-7 dígitos
                    if len(val) >= 10 and len(val) <= 15:
                        if sum(c.isalpha() for c in val) >= 4 and sum(c.isdigit() for c in val) >= 6:
                            container_number = val
                            break
            
            if not container_number or len(container_number) < 4:
                continue
            
            # Limpiar número de contenedor
            container_number = container_number.replace(' ', '').replace('-', '').upper()
            
            # Crear o actualizar contenedor
            container, created = Container.objects.get_or_create(
                container_number=container_number,
                defaults={
                    'container_type': '40ft',
                    'status': 'PROGRAMADO',
                    'owner_company': walmart_company,
                    'client': walmart_company,
                    'service_type': 'DIRECTO'
                }
            )
            
            # Actualizar información específica
            updated = False
            
            # Destino
            if 'destination' in mapped_columns:
                destino = normalize_text(str(row[mapped_columns['destination']]))
                if destino and destino != container.cd_location:
                    container.cd_location = destino
                    
                    # Determinar tipo de servicio por destino
                    destino_upper = destino.upper()
                    if any(cd in destino_upper for cd in ['QUILICURA', 'CAMPOS', 'MADERO']):
                        container.service_type = 'DIRECTO'
                    elif any(cd in destino_upper for cd in ['PENON', 'PEÑON']):
                        container.service_type = 'INDIRECTO_DEPOSITO'
                    
                    updated = True
            
            # Fecha de programación
            if 'date' in mapped_columns:
                fecha_str = str(row[mapped_columns['date']])
                if fecha_str and fecha_str != 'nan' and fecha_str != 'NaT':
                    try:
                        # Intentar múltiples formatos
                        date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d.%m.%Y']
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(fecha_str.split(' ')[0], fmt).date()
                                if parsed_date != container.scheduled_date:
                                    container.scheduled_date = parsed_date
                                    updated = True
                                break
                            except:
                                continue
                    except:
                        pass
            
            # Hora de programación
            if 'time' in mapped_columns:
                hora_str = str(row[mapped_columns['time']])
                if hora_str and hora_str != 'nan':
                    try:
                        time_formats = ['%H:%M', '%H:%M:%S', '%H.%M']
                        for fmt in time_formats:
                            try:
                                parsed_time = datetime.strptime(hora_str, fmt).time()
                                if parsed_time != container.scheduled_time:
                                    container.scheduled_time = parsed_time
                                    updated = True
                                break
                            except:
                                continue
                    except:
                        pass
            
            # Estado
            if 'status' in mapped_columns:
                status_str = normalize_text(str(row[mapped_columns['status']])).upper()
                status_map = {
                    'PROGRAMADO': 'PROGRAMADO',
                    'LIBERADO': 'LIBERADO',
                    'FINALIZADO': 'FINALIZADO',
                    'DESCARGADO': 'DESCARGADO',
                    'EN PROCESO': 'EN_PROCESO',
                    'PENDIENTE': 'PROGRAMADO'
                }
                
                for key, value in status_map.items():
                    if key in status_str:
                        if container.status != value:
                            container.status = value
                            updated = True
                        break
            
            # Guardar si hay cambios
            if updated or created:
                container.save()
            
            if created:
                containers_created += 1
            elif updated:
                containers_updated += 1
            
            containers_processed += 1
            
            if containers_processed % 10 == 0:
                print(f"  📦 Procesados: {containers_processed}")
                
        except Exception as e:
            print(f"⚠️ Error en registro {idx}: {e}")
            continue
    
    print(f"\n📊 RESUMEN PROCESAMIENTO WALMART:")
    print(f"✅ Registros procesados: {containers_processed}")
    print(f"🆕 Contenedores creados: {containers_created}")
    print(f"🔄 Contenedores actualizados: {containers_updated}")
    
    # Estadísticas finales
    total_walmart = Container.objects.filter(client=walmart_company).count()
    programados_walmart = Container.objects.filter(
        client=walmart_company, 
        status='PROGRAMADO'
    ).count()
    
    print(f"📦 Total contenedores Walmart: {total_walmart}")
    print(f"🎯 Programados para entrega: {programados_walmart}")
    
    return containers_processed > 0

def main():
    print("🚀 OPTIMIZADOR WALMART - SEPTIEMBRE 2025")
    print("=" * 50)
    
    success = process_walmart_september_data()
    
    if success:
        print("\n✅ Procesamiento exitoso")
        print("💡 Datos listos para optimización inteligente")
    else:
        print("\n❌ Error en procesamiento")
    
    print("\n🎉 Proceso completado")

if __name__ == "__main__":
    main()