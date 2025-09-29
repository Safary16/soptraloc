#!/usr/bin/env python
"""
Script específico para procesar la planilla de Walmart y extraer tiempos reales
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

def process_walmart_csv():
    """Procesar el CSV específico de Walmart"""
    
    csv_file = "PLANILLA MATRIZ IMPORTACIONES 3(WALMART).csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ No se encontró el archivo: {csv_file}")
        return
    
    print(f"📂 Procesando archivo: {csv_file}")
    
    try:
        # Leer CSV con punto y coma como separador
        df = pd.read_csv(csv_file, sep=';', encoding='latin-1')
        print(f"📊 Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
        
        # Mostrar columnas principales
        print("\n📋 Columnas principales encontradas:")
        key_columns = ['ID', 'Contenedor', 'CD', 'Fecha programación', 'Hora Programación', 
                      'FECHA ARRIBO EN CD', 'Hora', 'FechaDesg. (WHATSAPP/ Otawero)', 'HoraDesg',
                      'FechaDev', 'Terminal']
        
        for col in key_columns:
            if col in df.columns:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} (no encontrada)")
        
        # Analizar datos de tiempo
        analyze_walmart_times(df)
        
    except Exception as e:
        print(f"❌ Error procesando CSV: {str(e)}")
        import traceback
        traceback.print_exc()


def analyze_walmart_times(df):
    """Analizar los tiempos específicos de Walmart"""
    
    print(f"\n🔍 Analizando tiempos de {len(df)} contenedores de Walmart...")
    
    # Contadores
    containers_processed = 0
    times_updated = 0
    route_updates = {}
    
    for index, row in df.iterrows():
        try:
            # Extraer número de contenedor
            container_number = str(row.get('Contenedor', '')).strip()
            if not container_number or container_number == 'nan':
                continue
                
            # Limpiar número de contenedor (quitar sufijos como -6, -3, etc.)
            container_number = re.sub(r'-\d+$', '', container_number)
            
            # Extraer datos de tiempo
            times = extract_walmart_times(row)
            
            if times and len(times) >= 2:
                containers_processed += 1
                
                # Actualizar matriz de tiempos
                success = update_time_matrix_walmart(container_number, row, times)
                if success:
                    times_updated += 1
                
                # Mostrar progreso para primeros contenedores
                if containers_processed <= 5:
                    print(f"   📦 {container_number}")
                    print(f"      CD: {row.get('CD', 'N/A')}")
                    print(f"      Tiempos: {times}")
                    
        except Exception as e:
            continue
    
    print(f"\n📊 Resumen del análisis:")
    print(f"   📦 Contenedores procesados: {containers_processed}")
    print(f"   ⏱️  Matrices de tiempo actualizadas: {times_updated}")
    
    # Mostrar estadísticas de rutas actualizadas
    if route_updates:
        print(f"\n🛣️  Rutas con datos históricos actualizados:")
        for route, count in route_updates.items():
            print(f"     {route}: {count} actualizaciones")


def extract_walmart_times(row):
    """Extraer tiempos específicos de una fila de Walmart"""
    times = {}
    
    try:
        # Fecha y hora de programación
        fecha_prog = row.get('Fecha programación', '')
        hora_prog = row.get('Hora Programación', '')
        
        if fecha_prog and str(fecha_prog) != 'nan':
            prog_dt = parse_walmart_datetime(fecha_prog, hora_prog)
            if prog_dt:
                times['programacion'] = prog_dt
        
        # Fecha y hora de arribo en CD
        fecha_arribo = row.get('FECHA ARRIBO EN CD', '')
        hora_arribo = row.get('Hora', '')
        
        if fecha_arribo and str(fecha_arribo) != 'nan':
            arribo_dt = parse_walmart_datetime(fecha_arribo, hora_arribo)
            if arribo_dt:
                times['arribo_cd'] = arribo_dt
        
        # Fecha y hora de descarga
        fecha_desc = row.get('FechaDesg. (WHATSAPP/ Otawero)', '')
        hora_desc = row.get('HoraDesg', '')
        
        if fecha_desc and str(fecha_desc) != 'nan':
            desc_dt = parse_walmart_datetime(fecha_desc, hora_desc)
            if desc_dt:
                times['descarga'] = desc_dt
        
        # Fecha de devolución
        fecha_dev = row.get('FechaDev', '')
        if fecha_dev and str(fecha_dev) != 'nan':
            dev_dt = parse_walmart_datetime(fecha_dev)
            if dev_dt:
                times['devolucion'] = dev_dt
        
        # Calcular duraciones
        if len(times) >= 2:
            times['duraciones'] = calculate_walmart_durations(times)
        
    except Exception as e:
        pass
    
    return times


def parse_walmart_datetime(fecha, hora=None):
    """Parsear fecha y hora específica de Walmart"""
    try:
        if not fecha or str(fecha) == 'nan':
            return None
        
        fecha_str = str(fecha).strip()
        
        # Formato DD-MM-YY or DD/MM/YYYY
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, fecha_str)
            if match:
                day, month, year = match.groups()
                
                # Convertir año de 2 dígitos a 4
                if len(year) == 2:
                    year = '20' + year
                
                # Crear objeto datetime
                dt = datetime(int(year), int(month), int(day))
                
                # Agregar hora si está disponible
                if hora and str(hora) != 'nan':
                    hora_str = str(hora).strip()
                    
                    # Parsear hora HH:MM
                    time_match = re.match(r'(\d{1,2}):(\d{2})', hora_str)
                    if time_match:
                        hour, minute = time_match.groups()
                        dt = dt.replace(hour=int(hour), minute=int(minute))
                
                return dt
    
    except Exception as e:
        pass
    
    return None


def calculate_walmart_durations(times):
    """Calcular duraciones específicas de Walmart"""
    duraciones = {}
    
    try:
        # Ordenar tiempos por fecha
        sorted_times = sorted(times.items(), key=lambda x: x[1] if isinstance(x[1], datetime) else datetime.min)
        
        # Calcular duraciones entre eventos
        for i in range(len(sorted_times) - 1):
            event1, time1 = sorted_times[i]
            event2, time2 = sorted_times[i + 1]
            
            if isinstance(time1, datetime) and isinstance(time2, datetime):
                duration_minutes = (time2 - time1).total_seconds() / 60
                
                # Solo duraciones realistas
                if 0 <= duration_minutes <= 480:  # Hasta 8 horas
                    duraciones[f"{event1}_a_{event2}"] = int(duration_minutes)
        
        # Duraciones específicas importantes
        if 'programacion' in times and 'descarga' in times:
            duration = (times['descarga'] - times['programacion']).total_seconds() / 60
            if 30 <= duration <= 600:  # Entre 30 minutos y 10 horas
                duraciones['total_programacion_descarga'] = int(duration)
    
    except Exception as e:
        pass
    
    return duraciones


def update_time_matrix_walmart(container_number, row, times):
    """Actualizar matriz de tiempos con datos reales de Walmart"""
    
    try:
        from apps.drivers.models import Location, TimeMatrix
        
        # Determinar CD de destino
        cd_location = row.get('CD', '')
        if not cd_location or str(cd_location) == 'nan':
            return False
        
        print(f"      🔍 Procesando CD: '{cd_location}'")
        
        # Mapear CD a códigos de ubicación
        cd_mapping = {
            'quilicura': 'CD_QUILICURA',
            'campos': 'CD_CAMPOS',
            'madero': 'CD_MADERO',
            'peñón': 'CD_PENON',
            'penon': 'CD_PENON',
            'peï': 'CD_PENON',  # Para caracteres mal codificados
            'chillan': 'CD_CHILLAN',
            'chillï': 'CD_CHILLAN',  # Para caracteres mal codificados
            'temuco': 'CD_TEMUCO'
        }
        
        destino_code = None
        cd_lower = cd_location.lower()
        
        for key, code in cd_mapping.items():
            if key in cd_lower:
                destino_code = code
                print(f"         ✅ Mapeado: {cd_location} -> {destino_code}")
                break
        
        if not destino_code:
            print(f"         ❌ CD no mapeado: '{cd_location}'")
            return False
        
        # Origen generalmente es CCTI o puerto
        origen_code = 'CCTI'  # Por defecto
        terminal = row.get('Terminal', '')
        if terminal and 'sti' in str(terminal).lower():
            origen_code = 'CLEP'  # San Antonio
        
        # Obtener ubicaciones
        origen = Location.objects.filter(code=origen_code).first()
        destino = Location.objects.filter(code=destino_code).first()
        
        if not (origen and destino):
            print(f"         ❌ No se encontraron ubicaciones: {origen_code}, {destino_code}")
            return False
        
        print(f"         🏃 Ruta: {origen.name} -> {destino.name}")
        
        # Buscar matriz de tiempo
        time_matrix = TimeMatrix.objects.filter(
            from_location=origen,
            to_location=destino
        ).first()
        
        if not time_matrix:
            print(f"         ❌ No hay matriz de tiempo para {origen_code} -> {destino_code}")
            return False
        
        # Actualizar con tiempo real
        duraciones = times.get('duraciones', {})
        print(f"         📊 Duraciones disponibles: {list(duraciones.keys())}")
        
        # Buscar duración más relevante
        tiempo_real = None
        usado_key = None
        
        # Prioridades de duraciones - INCLUIR arribo_cd_a_descarga
        priority_keys = [
            'arribo_cd_a_descarga',  # Esta es la más importante para Walmart
            'total_programacion_descarga',
            'programacion_a_arribo_cd',
            'programacion_a_descarga'
        ]
        
        for key in priority_keys:
            if key in duraciones:
                tiempo_real = duraciones[key]
                usado_key = key
                break
        
        if tiempo_real and 30 <= tiempo_real <= 600:  # Entre 30 min y 10 horas
            time_matrix.update_historical_data(tiempo_real)
            print(f"         ⏱️  Actualizado con {tiempo_real} min (usando {usado_key})")
            return True
        else:
            print(f"         ⚠️  Tiempo no válido: {tiempo_real} min")
    
    except Exception as e:
        print(f"         ❌ Error: {e}")
    
    return False


def main():
    """Función principal"""
    print("🚀 Procesando datos reales de Walmart")
    print("=" * 50)
    
    process_walmart_csv()
    
    print("\n" + "=" * 50)
    print("✅ Procesamiento completado")
    
    # Estadísticas finales
    total_routes = TimeMatrix.objects.count()
    routes_with_history = TimeMatrix.objects.filter(avg_travel_time__isnull=False).count()
    
    print(f"\n📊 Estadísticas de matriz de tiempos:")
    print(f"   🛣️  Total de rutas: {total_routes}")
    print(f"   📈 Rutas con datos históricos: {routes_with_history}")
    if total_routes > 0:
        print(f"   🎯 Cobertura histórica: {(routes_with_history/total_routes)*100:.1f}%")
    
    # Mostrar algunas rutas con datos históricos
    historical_routes = TimeMatrix.objects.filter(avg_travel_time__isnull=False)[:5]
    if historical_routes:
        print(f"\n🔍 Ejemplos de rutas con datos históricos:")
        for route in historical_routes:
            print(f"   🛣️  {route.from_location.code} → {route.to_location.code}")
            print(f"      Tiempo teórico: {route.travel_time} min")
            print(f"      Tiempo promedio real: {route.avg_travel_time:.1f} min")
            print(f"      Viajes registrados: {route.total_trips}")


if __name__ == "__main__":
    main()