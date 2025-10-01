"""
Script simple para crear superusuario en Render
Ejecutar: python fix_admin_render.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'soptraloc_system'))

try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

print("\n" + "="*60)
print("🔧 SOLUCIONANDO PROBLEMA DE LOGIN")
print("="*60)

# 1. Ver usuarios actuales
print("\n1️⃣  Usuarios actuales en base de datos:")
total = User.objects.count()
print(f"   Total: {total}")

if total > 0:
    for user in User.objects.all():
        print(f"\n   - {user.username}")
        print(f"     Superusuario: {user.is_superuser}")
        print(f"     Staff: {user.is_staff}")
        print(f"     Activo: {user.is_active}")

# 2. Eliminar usuario admin si existe
print("\n2️⃣  Eliminando usuario 'admin' si existe...")
deleted_count = User.objects.filter(username='admin').delete()[0]
if deleted_count > 0:
    print(f"   ✅ Eliminado {deleted_count} usuario(s)")
else:
    print("   ℹ️  No había usuario 'admin' previo")

# 3. Crear nuevo superusuario
print("\n3️⃣  Creando superusuario 'admin'...")
try:
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@soptraloc.com',
        password='1234'
    )
    print("   ✅ SUPERUSUARIO CREADO")
    print(f"   Username: {admin.username}")
    print(f"   Email: {admin.email}")
    print(f"   ID: {admin.id}")
    print(f"   Superusuario: {admin.is_superuser}")
    print(f"   Staff: {admin.is_staff}")
    print(f"   Activo: {admin.is_active}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

# 4. Probar autenticación
print("\n4️⃣  Probando autenticación...")
user = authenticate(username='admin', password='1234')

if user is not None:
    print("   ✅ AUTENTICACIÓN EXITOSA")
    print(f"   Usuario autenticado: {user.username}")
else:
    print("   ❌ AUTENTICACIÓN FALLÓ")
    print("   ERROR: El usuario fue creado pero la autenticación no funciona")
    sys.exit(1)

# 5. Resumen final
print("\n" + "="*60)
print("✅ PROBLEMA SOLUCIONADO")
print("="*60)
print("\n🔗 Accede ahora a:")
print("   https://soptraloc.onrender.com/admin/")
print("\n🔐 Credenciales:")
print("   Usuario: admin")
print("   Password: 1234")
print("\n" + "="*60 + "\n")
