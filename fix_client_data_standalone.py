#!/usr/bin/env python
"""
Script de corrección de datos: Cliente vs Vendor
Ejecutar desde: Render Shell, VS Code, o cualquier terminal

USO:
    # Opción 1: Desde Render Shell
    cd /app/soptraloc_system
    python ../fix_client_data_standalone.py

    # Opción 2: Desde VS Code
    cd /workspaces/soptraloc/soptraloc_system
    python ../fix_client_data_standalone.py

    # Opción 3: Desde Django management
    python manage.py fix_client_vendor_data
"""

import os
import sys
import django

# Setup Django - Determinar path correcto
script_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(script_dir, 'soptraloc_system')

if not os.path.exists(django_dir):
    print("❌ Error: No se encuentra el directorio 'soptraloc_system'")
    print(f"   Buscado en: {django_dir}")
    print("\n💡 Asegúrate de ejecutar desde el directorio raíz del proyecto:")
    print("   cd /workspaces/soptraloc  (o /app en Render)")
    print("   python fix_client_data_standalone.py")
    sys.exit(1)

sys.path.insert(0, django_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'soptraloc_system.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Error al inicializar Django: {e}")
    print("\n💡 Intenta ejecutar desde el directorio Django:")
    print("   cd soptraloc_system")
    print("   python manage.py fix_client_vendor_data")
    sys.exit(1)

from apps.containers.models import Container
from apps.core.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()

def main():
    print("=" * 70)
    print("CORRECCIÓN AUTOMÁTICA: Cliente vs Vendor")
    print("=" * 70)
    
    # Obtener estadísticas iniciales
    total_containers = Container.objects.count()
    print(f"\n📊 Total de contenedores en BD: {total_containers}")
    
    if total_containers == 0:
        print("✅ No hay contenedores para procesar.")
        print("\n💡 Cuando importes nuevos datos, automáticamente tendrán 'Cliente Demo' como cliente.")
        return
    
    # Buscar contenedores con vendors como clientes
    containers_to_fix = Container.objects.exclude(client__name="CLIENTE DEMO")
    count_to_fix = containers_to_fix.count()
    
    print(f"\n🔍 Contenedores con vendor como cliente: {count_to_fix}")
    
    if count_to_fix == 0:
        print("✅ Todos los contenedores ya tienen 'Cliente Demo' como cliente.")
        print("✅ No se requiere corrección.")
        return
    
    # Mostrar vendors únicos que se van a reemplazar
    print("\n📋 Vendors actuales en campo 'client':")
    vendor_names = containers_to_fix.values_list('client__name', flat=True).distinct()
    for i, name in enumerate(vendor_names, 1):
        print(f"   {i}. {name}")
    
    # Confirmar acción
    print(f"\n⚠️  Se van a modificar {count_to_fix} contenedores")
    print("   Cambio: client = 'CLIENTE DEMO'")
    print("   owner_company se mantiene intacto (trazabilidad)")
    
    confirm = input("\n¿Continuar? (s/N): ").strip().lower()
    if confirm != 's':
        print("❌ Operación cancelada por el usuario.")
        return
    
    # Obtener o crear la compañía "Cliente Demo"
    print("\n🔧 Procesando...")
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        client_demo, created = Company.objects.get_or_create(
            name="CLIENTE DEMO",
            defaults={
                'company_type': 'CL',
                'created_by': admin_user
            }
        )
        
        if created:
            print(f"   ✅ Compañía 'Cliente Demo' creada")
        else:
            print(f"   ✅ Compañía 'Cliente Demo' encontrada (ID: {client_demo.id})")
        
        # Actualizar contenedores
        updated = 0
        for container in containers_to_fix:
            old_client = container.client.name if container.client else "N/A"
            container.client = client_demo
            container.save()
            updated += 1
            
            if updated % 10 == 0:
                print(f"   📦 Procesados: {updated}/{count_to_fix}")
        
        print(f"\n✅ COMPLETADO: {updated} contenedores actualizados")
        print("\n📊 Resumen:")
        print(f"   - Total contenedores: {total_containers}")
        print(f"   - Actualizados: {updated}")
        print(f"   - Con 'Cliente Demo': {Container.objects.filter(client=client_demo).count()}")
        
        print("\n🎉 ¡Corrección exitosa!")
        print("   Ahora todos los contenedores tienen 'Cliente Demo' como cliente.")
        print("   El campo 'owner_company' mantiene el vendor original para trazabilidad.")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la corrección: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
