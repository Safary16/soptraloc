#!/usr/bin/env python
"""
Script para extraer tiempos reales del Excel de Walmart y actualizar la matriz de tiempos
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
from apps.drivers.models import TimeMatrix, Location, Assignment
import pandas as pd
import re

def extract_real_times_from_csv():
    """Extraer tiempos reales del CSV de Walmart para mejorar la matriz de tiempos"""
    
    # Buscar el archivo CSV de Walmart
    csv_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.lower().endswith('.csv') and 'walmart' in file.lower():
                csv_files.append(os.path.join(root, file))
    
    if not csv_files:
        print("❌ No se encontró archivo CSV de Walmart")
        return
    
    csv_file = csv_files[0]
    print(f"📂 Procesando archivo: {csv_file}")
    
    try:
        # Leer el CSV con diferentes encodings y parámetros
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        
        for encoding in encodings:
            try:
                # Intentar con diferentes separadores y parámetros
                separators = [',', ';', '\t']
                
                for sep in separators:
                    try:
                        df = pd.read_csv(csv_file, encoding=encoding, separator=sep, 
                                       on_bad_lines='skip')
                        if len(df.columns) > 5:  # Si tiene columnas suficientes
                            print(f"✅ Archivo leído con encoding: {encoding}, separador: '{sep}'")
                            break
                    except Exception as e:
                        continue
                
                if df is not None and len(df.columns) > 5:
                    break
                    
            except Exception as e:
                continue
        
        # Si aún no funciona, intentar modo más permisivo
        if df is None or len(df.columns) <= 5:
            try:
                df = pd.read_csv(csv_file, encoding='latin-1', sep=None, engine='python',
                               on_bad_lines='skip')
                print(f"✅ Archivo leído con modo permisivo")
            except Exception as e:
                print(f"❌ Error final leyendo CSV: {str(e)}")
                return
        
        if df is None:
            print("❌ No se pudo leer el archivo CSV con ningún método")
            return
            
        print(f"📊 Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
        
        # Mostrar las primeras columnas para identificar estructura
        print("\n📋 Columnas disponibles:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1}. {col}")
        
        # Mostrar una muestra de los datos
        print("\n📋 Muestra de datos (primeras 3 filas):")
        for i, row in df.head(3).iterrows():
            print(f"   Fila {i+1}:")
            for col in df.columns[:8]:  # Solo primeras 8 columnas
                value = row[col] if pd.notna(row[col]) else "N/A"
                print(f"     {col}: {value}")
            print()
        
        # Analizar tiempos reales basados en las fechas y horas
        analyze_real_times(df)
        
    except Exception as e:
        print(f"❌ Error al procesar CSV: {str(e)}")
        import traceback
        traceback.print_exc()


def analyze_real_times(df):
    """Analizar tiempos reales del DataFrame"""
    
    print(f"\n🔍 Analizando tiempos reales...")
    
    # Buscar columnas de tiempo/fecha
    time_columns = []
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['fecha', 'hora', 'time', 'date', 'programacion', 'descarga', 'arribo']):
            time_columns.append(col)
    
    print(f"📅 Columnas de tiempo encontradas: {time_columns}")
    
    # Analizar datos por contenedor
    containers_analyzed = 0
    times_extracted = 0
    
    for index, row in df.iterrows():
        try:
            container_number = None
            
            # Buscar número de contenedor
            for col in df.columns:
                if pd.notna(row[col]) and isinstance(row[col], str):
                    # Patrón típico de contenedor: 4 letras + 7 números
                    container_pattern = r'[A-Z]{4}[0-9]{7}'
                    match = re.search(container_pattern, str(row[col]).upper())
                    if match:
                        container_number = match.group()
                        break
            
            if not container_number:
                continue
                
            containers_analyzed += 1
            
            # Extraer tiempos específicos
            times_data = extract_times_from_row(row, time_columns)
            
            if times_data:
                # Actualizar matriz de tiempos con datos reales
                update_time_matrix_with_real_data(container_number, times_data)
                times_extracted += 1
            
            if containers_analyzed <= 5:  # Mostrar primeros 5 para debug
                print(f"   📦 {container_number}: {times_data}")
                
        except Exception as e:
            continue
    
    print(f"\n📊 Resumen del análisis:")
    print(f"   📦 Contenedores analizados: {containers_analyzed}")
    print(f"   ⏱️  Tiempos extraídos: {times_extracted}")


def extract_times_from_row(row, time_columns):
    """Extraer tiempos específicos de una fila"""
    times_data = {}
    
    try:
        # Buscar diferentes tipos de tiempo
        for col in time_columns:
            if pd.notna(row[col]):
                col_lower = col.lower()
                value = row[col]
                
                # Programación
                if 'programacion' in col_lower or 'programada' in col_lower:
                    times_data['programacion'] = parse_datetime(value)
                
                # Arribo a CD
                elif 'arribo' in col_lower or 'llegada' in col_lower:
                    times_data['arribo_cd'] = parse_datetime(value)
                
                # Descarga
                elif 'descarga' in col_lower or 'gps' in col_lower:
                    times_data['descarga'] = parse_datetime(value)
                
                # Release/Liberación
                elif 'release' in col_lower or 'liberacion' in col_lower:
                    times_data['release'] = parse_datetime(value)
                
                # Retorno
                elif 'retorno' in col_lower or 'devolucion' in col_lower:
                    times_data['retorno'] = parse_datetime(value)
        
        # Calcular duraciones si tenemos suficientes datos
        if len(times_data) >= 2:
            calculate_durations(times_data)
        
    except Exception as e:
        pass
    
    return times_data


def parse_datetime(value):
    """Parsear diferentes formatos de fecha/hora"""
    if pd.isna(value):
        return None
        
    try:
        # Si ya es datetime
        if isinstance(value, datetime):
            return value
        
        # Si es string, intentar diferentes formatos
        if isinstance(value, str):
            # Formato DD/MM/YYYY HH:MM
            patterns = [
                '%d/%m/%Y %H:%M',
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d %H:%M:%S',
                '%d-%m-%Y %H:%M',
                '%d-%m-%Y %H:%M:%S'
            ]
            
            for pattern in patterns:
                try:
                    return datetime.strptime(value, pattern)
                except:
                    continue
        
        return None
        
    except:
        return None


def calculate_durations(times_data):
    """Calcular duraciones entre eventos"""
    durations = {}
    
    times_list = [
        ('programacion', 'programacion'),
        ('arribo_cd', 'arribo_cd'), 
        ('descarga', 'descarga'),
        ('release', 'release'),
        ('retorno', 'retorno')
    ]
    
    # Ordenar tiempos disponibles
    available_times = []
    for key, dt in times_data.items():
        if dt and isinstance(dt, datetime):
            available_times.append((key, dt))
    
    available_times.sort(key=lambda x: x[1])
    
    # Calcular duraciones entre eventos consecutivos
    for i in range(len(available_times) - 1):
        current_event, current_time = available_times[i]
        next_event, next_time = available_times[i + 1]
        
        duration_minutes = (next_time - current_time).total_seconds() / 60
        
        # Solo considerar duraciones realistas (entre 15 minutos y 8 horas)
        if 15 <= duration_minutes <= 480:
            durations[f"{current_event}_to_{next_event}"] = int(duration_minutes)
    
    times_data['durations'] = durations
    return durations


def update_time_matrix_with_real_data(container_number, times_data):
    """Actualizar matriz de tiempos con datos reales"""
    
    try:
        # Buscar el contenedor
        container = Container.objects.filter(container_number=container_number).first()
        if not container:
            return
        
        # Determinar origen y destino
        origen_code = 'CCTI'  # Asumimos CCTI como origen principal
        destino_code = None
        
        # Determinar destino basado en CD
        if container.cd_location:
            cd_mapping = {
                'quilicura': 'CD_QUILICURA',
                'campos': 'CD_CAMPOS', 
                'madero': 'CD_MADERO',
                'penon': 'CD_PENON'
            }
            
            cd_lower = container.cd_location.lower()
            for key, code in cd_mapping.items():
                if key in cd_lower:
                    destino_code = code
                    break
        
        if not destino_code:
            return
        
        # Obtener ubicaciones
        origen = Location.objects.filter(code=origen_code).first()
        destino = Location.objects.filter(code=destino_code).first()
        
        if not (origen and destino):
            return
        
        # Buscar matriz de tiempo existente
        time_matrix = TimeMatrix.objects.filter(
            from_location=origen,
            to_location=destino
        ).first()
        
        if not time_matrix:
            return
        
        # Actualizar con tiempo real si tenemos datos de duración
        durations = times_data.get('durations', {})
        
        # Buscar tiempo total del proceso
        total_time = None
        for key, duration in durations.items():
            # Si encontramos tiempo desde programación hasta descarga
            if 'programacion' in key and ('descarga' in key or 'arribo' in key):
                total_time = duration
                break
        
        if total_time and 30 <= total_time <= 300:  # Entre 30 min y 5 horas es realista
            # Actualizar datos históricos
            time_matrix.update_historical_data(total_time)
            print(f"   ⏱️  Actualizado {origen_code} → {destino_code}: {total_time} min (era {time_matrix.travel_time} min)")
    
    except Exception as e:
        pass


def main():
    """Función principal"""
    print("🚀 Extrayendo tiempos reales del CSV de Walmart")
    print("=" * 60)
    
    extract_real_times_from_csv()
    
    print("\n" + "=" * 60)
    print("✅ Análisis de tiempos reales completado")
    
    # Mostrar estadísticas de la matriz actualizada
    total_routes = TimeMatrix.objects.count()
    routes_with_history = TimeMatrix.objects.filter(avg_travel_time__isnull=False).count()
    
    print(f"📊 Estadísticas de matriz de tiempos:")
    print(f"   🛣️  Total de rutas: {total_routes}")
    print(f"   📈 Rutas con datos históricos: {routes_with_history}")
    if total_routes > 0:
        print(f"   🎯 Cobertura histórica: {(routes_with_history/total_routes)*100:.1f}%")
    else:
        print(f"   🎯 Cobertura histórica: 0.0%")


if __name__ == "__main__":
    main()