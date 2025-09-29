#!/usr/bin/env python
"""
Script para inicializar la matriz de tiempos entre ubicaciones del sistema SOPTRALOC.
Este script crea las ubicaciones principales y define los tiempos de traslado entre ellas.
"""

import os
import sys
import django
from datetime import datetime

# Agregar el path del proyecto
sys.path.append('/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from apps.drivers.models import Location, TimeMatrix


def create_locations():
    """Crear las ubicaciones principales del sistema"""
    
    locations_data = [
        # Terminales Portuarios
        {
            'name': 'CCTI - Centro de Contenedores Terminal Internacional',
            'code': 'CCTI',
            'address': 'Camino Melipilla Km 19, Maipú, Región Metropolitana',
            'latitude': -33.5167,
            'longitude': -70.7833
        },
        {
            'name': 'ZEAL - Terminal Puerto Valparaíso',
            'code': 'ZEAL',
            'address': 'Av. Errázuriz s/n, Valparaíso',
            'latitude': -33.0458,
            'longitude': -71.6197
        },
        {
            'name': 'CLEP - Terminal San Antonio',
            'code': 'CLEP',
            'address': 'Puerto San Antonio, Región de Valparaíso',
            'latitude': -33.5833,
            'longitude': -71.6167
        },
        
        # Centros de Distribución Walmart
        {
            'name': 'CD Quilicura - Centro de Distribución',
            'code': 'CD_QUILICURA',
            'address': 'Quilicura, Región Metropolitana',
            'latitude': -33.3606,
            'longitude': -70.7394
        },
        {
            'name': 'CD Campos de Chile - Pudahuel',
            'code': 'CD_CAMPOS',
            'address': 'Pudahuel, Región Metropolitana',
            'latitude': -33.3775,
            'longitude': -70.7947
        },
        {
            'name': 'CD Puerto Madero - Pudahuel',
            'code': 'CD_MADERO',
            'address': 'Pudahuel, Región Metropolitana',
            'latitude': -33.3889,
            'longitude': -70.7608
        },
        {
            'name': 'CD El Peñón - San Bernardo',
            'code': 'CD_PENON',
            'address': 'San Bernardo, Región Metropolitana',
            'latitude': -33.5983,
            'longitude': -70.7014
        },
        {
            'name': 'CD Chillán',
            'code': 'CD_CHILLAN',
            'address': 'Chillán, Región de Ñuble',
            'latitude': -36.6061,
            'longitude': -72.1039
        },
        {
            'name': 'CD Temuco',
            'code': 'CD_TEMUCO',
            'address': 'Temuco, Región de la Araucanía',
            'latitude': -38.7359,
            'longitude': -72.5986
        },
        
        # Ubicaciones Intermedias
        {
            'name': 'Almacén Extraportuario',
            'code': 'ALMACEN_EXTRA',
            'address': 'Región Metropolitana',
            'latitude': -33.4569,
            'longitude': -70.6483
        },
        {
            'name': 'Depósito de Devolución',
            'code': 'DEPOSITO_DEV',
            'address': 'Región Metropolitana',
            'latitude': -33.4569,
            'longitude': -70.6483
        }
    ]
    
    created_locations = []
    
    for loc_data in locations_data:
        location, created = Location.objects.get_or_create(
            code=loc_data['code'],
            defaults={
                'name': loc_data['name'],
                'address': loc_data['address'],
                'latitude': loc_data['latitude'],
                'longitude': loc_data['longitude']
            }
        )
        
        if created:
            print(f"✅ Creada ubicación: {location.name}")
        else:
            print(f"📍 Ubicación existente: {location.name}")
            
        created_locations.append(location)
    
    return created_locations


def create_time_matrix():
    """Crear la matriz de tiempos entre ubicaciones"""
    
    # Obtener todas las ubicaciones
    locations = Location.objects.all()
    location_dict = {loc.code: loc for loc in locations}
    
    # Matriz de tiempos (en minutos) - basada en TIEMPOS REALES OPERATIVOS
    time_data = {
        # Desde CCTI
        'CCTI': {
            'CD_QUILICURA': {'travel': 60, 'loading': 30, 'unloading': 45},  # 1 hora real
            'CD_CAMPOS': {'travel': 40, 'loading': 30, 'unloading': 45},     # 40 min real
            'CD_MADERO': {'travel': 40, 'loading': 30, 'unloading': 45},     # 40 min real
            'CD_PENON': {'travel': 60, 'loading': 30, 'unloading': 45},      # 1 hora real
            'CD_CHILLAN': {'travel': 330, 'loading': 30, 'unloading': 60},
            'CD_TEMUCO': {'travel': 450, 'loading': 30, 'unloading': 60},
            'ZEAL': {'travel': 90, 'loading': 60, 'unloading': 30},          # 1h 30min real
            'CLEP': {'travel': 90, 'loading': 60, 'unloading': 30},          # 1h 30min real
            'ALMACEN_EXTRA': {'travel': 50, 'loading': 20, 'unloading': 20},
            'DEPOSITO_DEV': {'travel': 40, 'loading': 15, 'unloading': 15},
        },
        
        # Desde ZEAL (Valparaíso) - Tiempos reales operativos
        'ZEAL': {
            'CCTI': {'travel': 90, 'loading': 40, 'unloading': 40},          # 1h 30min real + carga/desc 40min
            'CD_QUILICURA': {'travel': 120, 'loading': 40, 'unloading': 45}, # 2h real a CD
            'CD_CAMPOS': {'travel': 120, 'loading': 40, 'unloading': 45},    # 2h real a CD
            'CD_MADERO': {'travel': 120, 'loading': 40, 'unloading': 45},    # 2h real a CD
            'CD_PENON': {'travel': 120, 'loading': 40, 'unloading': 45},     # 2h real a CD
            'CD_CHILLAN': {'travel': 420, 'loading': 40, 'unloading': 60},
            'CD_TEMUCO': {'travel': 540, 'loading': 40, 'unloading': 60},
            'CLEP': {'travel': 30, 'loading': 40, 'unloading': 40},
            'ALMACEN_EXTRA': {'travel': 140, 'loading': 40, 'unloading': 20},
        },
        
        # Desde CLEP (San Antonio) - Tiempos reales operativos
        'CLEP': {
            'CCTI': {'travel': 90, 'loading': 40, 'unloading': 40},          # 1h 30min real + carga/desc 40min
            'CD_QUILICURA': {'travel': 120, 'loading': 40, 'unloading': 45}, # 2h real a CD
            'CD_CAMPOS': {'travel': 120, 'loading': 40, 'unloading': 45},    # 2h real a CD
            'CD_MADERO': {'travel': 120, 'loading': 40, 'unloading': 45},    # 2h real a CD
            'CD_PENON': {'travel': 120, 'loading': 40, 'unloading': 45},     # 2h real a CD
            'CD_CHILLAN': {'travel': 450, 'loading': 40, 'unloading': 60},
            'CD_TEMUCO': {'travel': 570, 'loading': 40, 'unloading': 60},
            'ZEAL': {'travel': 30, 'loading': 40, 'unloading': 40},
            'ALMACEN_EXTRA': {'travel': 170, 'loading': 40, 'unloading': 20},
        },        # Desde ZEAL
        'ZEAL': {
            'CCTI': {'travel': 90, 'loading': 30, 'unloading': 30},
            'CD_QUILICURA': {'travel': 120, 'loading': 30, 'unloading': 45},
            'CD_CAMPOS': {'travel': 110, 'loading': 30, 'unloading': 45},
            'CD_MADERO': {'travel': 115, 'loading': 30, 'unloading': 45},
            'CD_PENON': {'travel': 140, 'loading': 30, 'unloading': 45},
            'CLEP': {'travel': 45, 'loading': 30, 'unloading': 30},
            'ALMACEN_EXTRA': {'travel': 100, 'loading': 20, 'unloading': 20},
        },
        
        # Desde CLEP
        'CLEP': {
            'CCTI': {'travel': 120, 'loading': 30, 'unloading': 30},
            'CD_QUILICURA': {'travel': 150, 'loading': 30, 'unloading': 45},
            'CD_CAMPOS': {'travel': 140, 'loading': 30, 'unloading': 45},
            'CD_MADERO': {'travel': 145, 'loading': 30, 'unloading': 45},
            'CD_PENON': {'travel': 130, 'loading': 30, 'unloading': 45},
            'ZEAL': {'travel': 45, 'loading': 30, 'unloading': 30},
            'ALMACEN_EXTRA': {'travel': 130, 'loading': 20, 'unloading': 20},
        },
        
        # Entre CDs (para transferencias)
                # Entre CDs - Tiempos reales basados en distancias operativas
        'CD_QUILICURA': {
            'CD_CAMPOS': {'travel': 25, 'loading': 15, 'unloading': 15},
            'CD_MADERO': {'travel': 20, 'loading': 15, 'unloading': 15},
            'CD_PENON': {'travel': 60, 'loading': 15, 'unloading': 15},     # Ajustado proporcionalmente
            'CD_CHILLAN': {'travel': 300, 'loading': 15, 'unloading': 30},
            'CD_TEMUCO': {'travel': 420, 'loading': 15, 'unloading': 30},
            'DEPOSITO_DEV': {'travel': 35, 'loading': 15, 'unloading': 15},
        },
        
        'CD_CAMPOS': {
            'CD_QUILICURA': {'travel': 25, 'loading': 15, 'unloading': 15},
            'CD_MADERO': {'travel': 10, 'loading': 15, 'unloading': 15},    # Muy cerca, ajustado
            'CD_PENON': {'travel': 50, 'loading': 15, 'unloading': 15},     # Ajustado proporcionalmente
            'CD_CHILLAN': {'travel': 290, 'loading': 15, 'unloading': 30},
            'CD_TEMUCO': {'travel': 410, 'loading': 15, 'unloading': 30},
            'DEPOSITO_DEV': {'travel': 30, 'loading': 15, 'unloading': 15},
        },
        
        'CD_MADERO': {
            'CD_QUILICURA': {'travel': 20, 'loading': 15, 'unloading': 15},
            'CD_CAMPOS': {'travel': 10, 'loading': 15, 'unloading': 15},
            'CD_PENON': {'travel': 50, 'loading': 15, 'unloading': 15},     # Ajustado proporcionalmente
            'CD_CHILLAN': {'travel': 295, 'loading': 15, 'unloading': 30},
            'CD_TEMUCO': {'travel': 415, 'loading': 15, 'unloading': 30},
            'DEPOSITO_DEV': {'travel': 25, 'loading': 15, 'unloading': 15},
        },
        
        'CD_PENON': {
            'CD_QUILICURA': {'travel': 60, 'loading': 15, 'unloading': 15},
            'CD_CAMPOS': {'travel': 50, 'loading': 15, 'unloading': 15},
            'CD_MADERO': {'travel': 50, 'loading': 15, 'unloading': 15},
            'CD_CHILLAN': {'travel': 300, 'loading': 15, 'unloading': 30},
            'CD_TEMUCO': {'travel': 420, 'loading': 15, 'unloading': 30},
            'DEPOSITO_DEV': {'travel': 45, 'loading': 15, 'unloading': 15},
        },
        
        'CD_CHILLAN': {
            'CD_QUILICURA': {'travel': 300, 'loading': 15, 'unloading': 15},
            'CD_CAMPOS': {'travel': 290, 'loading': 15, 'unloading': 15},
            'CD_MADERO': {'travel': 295, 'loading': 15, 'unloading': 15},
            'CD_PENON': {'travel': 300, 'loading': 15, 'unloading': 15},
            'CD_TEMUCO': {'travel': 120, 'loading': 15, 'unloading': 30},
            'DEPOSITO_DEV': {'travel': 320, 'loading': 15, 'unloading': 15},
        },
        
        'CD_TEMUCO': {
            'CD_QUILICURA': {'travel': 420, 'loading': 15, 'unloading': 15},
            'CD_CAMPOS': {'travel': 410, 'loading': 15, 'unloading': 15},
            'CD_MADERO': {'travel': 415, 'loading': 15, 'unloading': 15},
            'CD_PENON': {'travel': 420, 'loading': 15, 'unloading': 15},
            'CD_CHILLAN': {'travel': 120, 'loading': 15, 'unloading': 30},
            'DEPOSITO_DEV': {'travel': 440, 'loading': 15, 'unloading': 15},
        },
    }
    
    created_count = 0
    updated_count = 0
    
    for from_code, destinations in time_data.items():
        if from_code not in location_dict:
            print(f"⚠️ Ubicación origen no encontrada: {from_code}")
            continue
            
        from_location = location_dict[from_code]
        
        for to_code, times in destinations.items():
            if to_code not in location_dict:
                print(f"⚠️ Ubicación destino no encontrada: {to_code}")
                continue
                
            to_location = location_dict[to_code]
            
            time_matrix, created = TimeMatrix.objects.get_or_create(
                from_location=from_location,
                to_location=to_location,
                defaults={
                    'travel_time': times['travel'],
                    'loading_time': times['loading'],
                    'unloading_time': times['unloading']
                }
            )
            
            if created:
                created_count += 1
                print(f"✅ Creada ruta: {from_code} → {to_code} ({times['travel']}min)")
            else:
                # Actualizar si es diferente
                if (time_matrix.travel_time != times['travel'] or 
                    time_matrix.loading_time != times['loading'] or 
                    time_matrix.unloading_time != times['unloading']):
                    
                    time_matrix.travel_time = times['travel']
                    time_matrix.loading_time = times['loading']
                    time_matrix.unloading_time = times['unloading']
                    time_matrix.save()
                    
                    updated_count += 1
                    print(f"🔄 Actualizada ruta: {from_code} → {to_code} ({times['travel']}min)")
                else:
                    print(f"📍 Ruta existente: {from_code} → {to_code}")
    
    print(f"\n📊 Resumen:")
    print(f"   - Rutas creadas: {created_count}")
    print(f"   - Rutas actualizadas: {updated_count}")
    
    return created_count, updated_count


def create_reverse_routes():
    """Crear rutas de retorno automáticamente"""
    
    existing_routes = TimeMatrix.objects.all()
    created_count = 0
    
    for route in existing_routes:
        # Verificar si existe la ruta inversa
        reverse_exists = TimeMatrix.objects.filter(
            from_location=route.to_location,
            to_location=route.from_location
        ).exists()
        
        if not reverse_exists:
            # Crear ruta inversa con tiempos similares
            # Los tiempos de retorno suelen ser similares, pero con menos tiempo de carga
            reverse_route = TimeMatrix.objects.create(
                from_location=route.to_location,
                to_location=route.from_location,
                travel_time=route.travel_time,
                loading_time=15,  # Tiempo estándar para carga de retorno
                unloading_time=15  # Tiempo estándar para descarga de retorno
            )
            
            created_count += 1
            print(f"🔄 Creada ruta inversa: {reverse_route.from_location.code} → {reverse_route.to_location.code}")
    
    print(f"\n📊 Rutas inversas creadas: {created_count}")
    return created_count


def main():
    """Función principal"""
    
    print("🚀 Inicializando sistema de gestión de tiempos SOPTRALOC")
    print("=" * 60)
    
    # 1. Crear ubicaciones
    print("\n1️⃣ Creando ubicaciones...")
    locations = create_locations()
    print(f"   Total ubicaciones: {len(locations)}")
    
    # 2. Crear matriz de tiempos
    print("\n2️⃣ Creando matriz de tiempos...")
    created, updated = create_time_matrix()
    
    # 3. Crear rutas inversas
    print("\n3️⃣ Creando rutas de retorno...")
    reverse_created = create_reverse_routes()
    
    # 4. Estadísticas finales
    total_routes = TimeMatrix.objects.count()
    total_locations = Location.objects.count()
    
    print("\n" + "=" * 60)
    print("🎉 INICIALIZACIÓN COMPLETADA")
    print("=" * 60)
    print(f"📍 Ubicaciones totales: {total_locations}")
    print(f"🛣️  Rutas totales: {total_routes}")
    print(f"✨ Rutas nuevas: {created}")
    print(f"🔄 Rutas actualizadas: {updated}")
    print(f"↩️  Rutas inversas creadas: {reverse_created}")
    
    print("\n💡 El sistema ahora puede:")
    print("   - Calcular tiempos de traslado automáticamente")
    print("   - Verificar disponibilidad de conductores")
    print("   - Optimizar asignaciones basado en horarios")
    print("   - Aprender de datos históricos")
    
    print(f"\n⏰ Proceso completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()