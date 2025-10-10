#!/usr/bin/env python
"""
Script para aplicar reparaciones masivas al código detectadas en la auditoría.
Ejecutar: python apply_fixes.py
"""
import os
import re
from pathlib import Path

FIXES_APPLIED = []

def fix_csrf_exempt(file_path):
    """Eliminar @csrf_exempt de views"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    # Eliminar @csrf_exempt decorator
    content = re.sub(r'@csrf_exempt\s*\n', '', content)
    # Eliminar import si existe
    content = re.sub(r'from django\.views\.decorators\.csrf import csrf_exempt\s*\n', '', content)
    
    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        FIXES_APPLIED.append(f"✅ Removed @csrf_exempt from {file_path}")
        return True
    return False

def add_select_related(file_path):
    """Agregar select_related donde falta"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern: Container.objects.all() sin select_related
    pattern = r'Container\.objects\.all\(\)'
    replacement = "Container.objects.select_related('owner_company', 'client', 'current_location').all()"
    content = re.sub(pattern, replacement, content)
    
    # Pattern: Container.objects.filter() sin select_related
    pattern = r'Container\.objects\.filter\('
    replacement = "Container.objects.select_related('owner_company', 'client', 'current_location').filter("
    content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        FIXES_APPLIED.append(f"✅ Added select_related to {file_path}")
        return True
    return False

def fix_fields_all(file_path):
    """Cambiar fields='__all__' por lista explícita en serializers"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original = content
    
    # Detectar serializers con fields='__all__'
    if "fields = '__all__'" in content:
        print(f"⚠️  WARNING: {file_path} tiene fields='__all__' - revisar manualmente")
        # No lo cambiamos automáticamente porque requiere conocer los campos
    
    return False

def main():
    print("🔧 APLICANDO REPARACIONES MASIVAS")
    print("="*80)
    
    # Directorio de apps
    apps_dir = Path('soptraloc_system/apps')
    
    if not apps_dir.exists():
        print(f"❌ Directorio {apps_dir} no encontrado")
        return
    
    # Fix 1: Eliminar @csrf_exempt
    print("\n1️⃣  Eliminando @csrf_exempt...")
    for views_file in apps_dir.rglob('views.py'):
        fix_csrf_exempt(views_file)
    
    # Fix 2: Agregar select_related
    print("\n2️⃣  Agregando select_related...")
    for views_file in apps_dir.rglob('views.py'):
        add_select_related(views_file)
    
    # Fix 3: Verificar serializers
    print("\n3️⃣  Verificando serializers...")
    for serializer_file in apps_dir.rglob('serializers.py'):
        fix_fields_all(serializer_file)
    
    # Resumen
    print("\n" + "="*80)
    print(f"📊 RESUMEN: {len(FIXES_APPLIED)} reparaciones aplicadas")
    print("="*80)
    for fix in FIXES_APPLIED:
        print(fix)
    
    if not FIXES_APPLIED:
        print("✅ No se encontraron problemas para reparar")
    
    print("\n⚠️  SIGUIENTE PASO: Ejecutar migrations")
    print("cd soptraloc_system")
    print("python manage.py makemigrations")
    print("python manage.py migrate")

if __name__ == '__main__':
    main()
