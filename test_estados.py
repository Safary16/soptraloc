#!/usr/bin/env python
"""
Script de prueba para verificar transiciones de estados
Simula el ciclo de vida completo de un contenedor
"""
import os
import sys
import django

# Setup Django
sys.path.append('/workspaces/soptraloc')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container
from apps.cds.models import CD
from django.utils import timezone
from datetime import timedelta


def crear_contenedor_prueba():
    """Crea un contenedor de prueba"""
    container = Container.objects.create(
        container_id='TEST1234567',
        tipo='40',
        nave='NAVE PRUEBA',
        fecha_eta=timezone.now() + timedelta(days=1),
        peso=25000,
        vendor='Vendor Test',
        puerto='Valparaíso',
        estado='por_arribar',
        comuna='Pudahuel'
    )
    print(f"✅ Contenedor creado: {container.container_id}")
    return container


def test_ciclo_completo(container):
    """Prueba todas las transiciones de estado"""
    
    print("\n🔄 Iniciando ciclo de vida completo...\n")
    
    # 1. Arribado
    print("1️⃣ Marcando como ARRIBADO (nave llegó)...")
    container.cambiar_estado('arribado')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha arribo: {container.fecha_arribo}")
    
    # 2. Liberado
    print("\n2️⃣ Marcando como LIBERADO (aduana aprobó)...")
    container.cambiar_estado('liberado')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha liberación: {container.fecha_liberacion}")
    
    # 3. Secuenciado
    print("\n3️⃣ Marcando como SECUENCIADO...")
    container.cambiar_estado('secuenciado')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    
    # 4. Programado
    print("\n4️⃣ Marcando como PROGRAMADO (asignado a fecha y CD)...")
    container.cambiar_estado('programado')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha programación: {container.fecha_programacion}")
    
    # 5. Asignado
    print("\n5️⃣ Marcando como ASIGNADO (conductor asignado)...")
    container.cambiar_estado('asignado')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha asignación: {container.fecha_asignacion}")
    
    # 6. En Ruta
    print("\n6️⃣ Marcando como EN RUTA (conductor salió)...")
    container.cambiar_estado('en_ruta')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha inicio ruta: {container.fecha_inicio_ruta}")
    
    # 7. Entregado
    print("\n7️⃣ Marcando como ENTREGADO (llegó a CD)...")
    container.cambiar_estado('entregado')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha entrega: {container.fecha_entrega}")
    
    # 8. Descargado
    print("\n8️⃣ Marcando como DESCARGADO (cliente descargó)...")
    container.cambiar_estado('descargado')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha descarga: {container.fecha_descarga}")
    
    # 9. Vacío
    print("\n9️⃣ Marcando como VACÍO (esperando retiro)...")
    container.cambiar_estado('vacio')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha vacío: {container.fecha_vacio}")
    
    # 10. Vacío en Ruta
    print("\n🔟 Marcando como VACÍO EN RUTA (retornando)...")
    container.cambiar_estado('vacio_en_ruta')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha vacío ruta: {container.fecha_vacio_ruta}")
    
    # 11. Devuelto
    print("\n1️⃣1️⃣ Marcando como DEVUELTO (en depósito naviera)...")
    container.cambiar_estado('devuelto')
    print(f"   ✅ Estado: {container.get_estado_display()}")
    print(f"   📅 Fecha devolución: {container.fecha_devolucion}")
    
    print("\n" + "="*60)
    print("🎉 CICLO DE VIDA COMPLETO FINALIZADO")
    print("="*60)


def mostrar_resumen(container):
    """Muestra resumen de todos los timestamps"""
    print("\n📊 RESUMEN DE TIMESTAMPS:\n")
    timestamps = [
        ('Arribo', container.fecha_arribo),
        ('Liberación', container.fecha_liberacion),
        ('Programación', container.fecha_programacion),
        ('Asignación', container.fecha_asignacion),
        ('Inicio Ruta', container.fecha_inicio_ruta),
        ('Entrega', container.fecha_entrega),
        ('Descarga', container.fecha_descarga),
        ('Vacío', container.fecha_vacio),
        ('Vacío Ruta', container.fecha_vacio_ruta),
        ('Devolución', container.fecha_devolucion),
    ]
    
    for label, timestamp in timestamps:
        if timestamp:
            print(f"✅ {label:20}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"❌ {label:20}: No registrado")


def limpiar_contenedor_prueba(container):
    """Elimina el contenedor de prueba"""
    container_id = container.container_id
    container.delete()
    print(f"\n🗑️ Contenedor {container_id} eliminado")


def main():
    print("\n" + "="*60)
    print("🧪 TEST DE ESTADOS - CICLO DE VIDA COMPLETO")
    print("="*60)
    
    try:
        # Verificar que existan CDs
        cd_count = CD.objects.count()
        print(f"\n📍 CDs disponibles: {cd_count}")
        if cd_count == 0:
            print("⚠️ No hay CDs configurados. Ejecuta: python manage.py init_cds")
        
        # Crear contenedor de prueba
        container = crear_contenedor_prueba()
        
        # Ejecutar ciclo completo
        test_ciclo_completo(container)
        
        # Mostrar resumen
        mostrar_resumen(container)
        
        # Preguntar si eliminar
        respuesta = input("\n¿Eliminar contenedor de prueba? (s/n): ")
        if respuesta.lower() == 's':
            limpiar_contenedor_prueba(container)
        else:
            print(f"\n✅ Contenedor {container.container_id} conservado para inspección")
        
        print("\n✅ Test completado exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error durante el test: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
