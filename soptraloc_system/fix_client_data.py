#!/usr/bin/env python
"""
Script para corregir datos de clientes en contenedores existentes.

Problema: Los contenedores importados antes del fix tienen vendors como clientes.
Solución: Actualizar todos los contenedores para que client = "Cliente Demo"

Ejecución: python manage.py shell < fix_client_data.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container
from django.contrib.auth import get_user_model

User = get_user_model()

def fix_client_data():
    """Corrige los datos de cliente en todos los contenedores."""
    
    print("\n" + "="*70)
    print("CORRECCIÓN DE DATOS: Cliente vs Vendor")
    print("="*70)
    
    # Obtener todos los contenedores
    containers = Container.objects.select_related('client', 'owner_company').all()
    total = containers.count()
    
    print(f"\n📊 Total de contenedores en BD: {total}")
    
    if total == 0:
        print("✅ No hay contenedores para procesar.")
        return
    
    # Mostrar estado actual (primeros 5)
    print("\n📋 ESTADO ACTUAL (primeros 5):")
    print("-" * 70)
    for container in containers[:5]:
        client_name = container.client.name if container.client else "NULL"
        owner_name = container.owner_company.name if container.owner_company else "NULL"
        print(f"  {container.container_number:15} | Cliente: {client_name:30} | Owner: {owner_name}")
    
    # Identificar contenedores con problema
    problematic = []
    for container in containers:
        # Si el cliente NO es "Cliente Demo", hay problema
        if not container.client or container.client.name != "Cliente Demo":
            problematic.append(container)
    
    print(f"\n⚠️  Contenedores con problema: {len(problematic)}")
    
    if len(problematic) == 0:
        print("✅ Todos los contenedores tienen 'Cliente Demo' correctamente.")
        return
    
    # Obtener o crear "Cliente Demo"
    from apps.containers.services.excel_importers import _get_or_create_company
    
    # Necesitamos un usuario para crear la compañía
    user = User.objects.first()
    if not user:
        print("❌ ERROR: No hay usuarios en el sistema. No se puede crear 'Cliente Demo'.")
        return
    
    print(f"\n🔧 Usando usuario: {user.email}")
    
    # Crear o obtener "Cliente Demo"
    client_demo = _get_or_create_company("Cliente Demo", user)
    print(f"✅ Cliente Demo: {client_demo.name} (ID: {client_demo.id})")
    
    # Actualizar contenedores
    print(f"\n🔄 Actualizando {len(problematic)} contenedores...")
    print("-" * 70)
    
    updated_count = 0
    for container in problematic:
        old_client = container.client.name if container.client else "NULL"
        container.client = client_demo
        container.save()
        updated_count += 1
        
        if updated_count <= 10:  # Mostrar primeros 10
            print(f"  ✓ {container.container_number:15} | {old_client:30} → Cliente Demo")
    
    if updated_count > 10:
        print(f"  ... y {updated_count - 10} más")
    
    # Verificar resultado
    print("\n" + "="*70)
    print("VERIFICACIÓN FINAL")
    print("="*70)
    
    containers_updated = Container.objects.select_related('client', 'owner_company').all()
    
    print("\n📋 ESTADO FINAL (primeros 5):")
    print("-" * 70)
    for container in containers_updated[:5]:
        client_name = container.client.name if container.client else "NULL"
        owner_name = container.owner_company.name if container.owner_company else "NULL"
        status_icon = "✅" if client_name == "Cliente Demo" else "❌"
        print(f"  {status_icon} {container.container_number:15} | Cliente: {client_name:30} | Owner: {owner_name}")
    
    # Contar por estado
    demo_count = Container.objects.filter(client__name="Cliente Demo").count()
    other_count = total - demo_count
    
    print(f"\n📊 RESUMEN:")
    print(f"  ✅ Cliente Demo: {demo_count}")
    print(f"  ❌ Otros clientes: {other_count}")
    print(f"  📦 Total: {total}")
    
    if other_count == 0:
        print("\n🎉 ¡ÉXITO! Todos los contenedores tienen 'Cliente Demo'")
    else:
        print(f"\n⚠️  ADVERTENCIA: {other_count} contenedores aún no tienen 'Cliente Demo'")
    
    print("\n" + "="*70)
    print(f"✅ Proceso completado: {updated_count} contenedores actualizados")
    print("="*70 + "\n")

if __name__ == "__main__":
    fix_client_data()
