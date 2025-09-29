#!/usr/bin/env python3
"""
Actualizar tipos de servicio basado en operación real SOPTRALOC
Drop & Hook vs Descarga sobre Camión
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.drivers.models import Location, TimeMatrix
from apps.containers.models import Container

def update_service_types():
    """Actualizar tipos de servicio según operación real"""
    
    print("🚛 ACTUALIZANDO TIPOS DE SERVICIO SOPTRALOC")
    print("=" * 60)
    
    # Obtener ubicaciones
    ccti = Location.objects.get(code='CCTI')
    clep = Location.objects.get(code='CLEP')
    zeal = Location.objects.get(code='ZEAL')
    
    quilicura = Location.objects.get(code='CD_QUILICURA')
    campos = Location.objects.get(code='CD_CAMPOS')
    madero = Location.objects.get(code='CD_MADERO')
    penon = Location.objects.get(code='CD_PENON')
    
    print("\n📋 TIPOS DE SERVICIO IDENTIFICADOS:")
    print("-" * 40)
    
    # TIPO 1: Terminales → CDs con DESCARGA SOBRE CAMIÓN
    print("1️⃣  DESCARGA SOBRE CAMIÓN (Quilicura, Campos, Madero)")
    print("   • Terminal → CCTI: 1h 30min")
    print("   • Carga en terminal: 40min") 
    print("   • CCTI/Terminal → CD: 2h")
    print("   • Descarga en CD: 2h (120min)")
    print("   • TOTAL: ~6h (360min)")
    
    # Actualizar tiempos para descarga sobre camión
    cds_descarga_camion = [quilicura, campos, madero]
    
    for terminal in [clep, zeal]:
        for cd in cds_descarga_camion:
            try:
                # Ruta directa terminal → CD (servicio completo)
                matrix_direct = TimeMatrix.objects.get(from_location=terminal, to_location=cd)
                matrix_direct.travel_time = 120  # 2h viaje
                matrix_direct.loading_time = 40   # 40min carga terminal
                matrix_direct.unloading_time = 120 # 2h descarga sobre camión
                matrix_direct.save()
                
                print(f"   ✅ {terminal.code} → {cd.code}: 120+40+120 = 280min total")
                
            except TimeMatrix.DoesNotExist:
                print(f"   ⚠️  Matriz no existe: {terminal.code} → {cd.code}")
    
    print("\n2️⃣  DROP & HOOK (El Peñón)")
    print("   • CCTI → El Peñón: 1h")
    print("   • Solo suelta contenedor: ~15min")
    print("   • Puede tomar vacío de vuelta")
    print("   • TOTAL: ~1h 15min (75min)")
    
    # Actualizar tiempos para drop & hook
    try:
        matrix_penon = TimeMatrix.objects.get(from_location=ccti, to_location=penon)
        matrix_penon.travel_time = 60   # 1h viaje
        matrix_penon.loading_time = 30  # Carga en CCTI
        matrix_penon.unloading_time = 15 # Solo suelta
        matrix_penon.save()
        
        print(f"   ✅ CCTI → El Peñón: 60+30+15 = 105min total")
        
    except TimeMatrix.DoesNotExist:
        print("   ⚠️  Matriz CCTI → El Peñón no existe")
    
    print("\n3️⃣  MODALIDAD DUAL (Dos opciones)")
    print("   • Opción A: Mismo conductor todo el viaje")
    print("   • Opción B: Deja en CCTI + conductor local")
    print("   • Sistema debe permitir ambas opciones")
    
    print("\n" + "=" * 60)
    print("✅ ACTUALIZACIÓN DE SERVICIOS COMPLETADA")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Agregar campo 'service_type' a Container")
    print("   2. Implementar lógica de asignación por tipo")
    print("   3. Interface para seleccionar modalidad")

if __name__ == "__main__":
    update_service_types()