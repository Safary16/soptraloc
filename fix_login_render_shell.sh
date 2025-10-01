#!/usr/bin/env bash
# Script para ejecutar EN RENDER SHELL y solucionar el problema de login

echo "======================================================"
echo "🔧 SOLUCIÓN INMEDIATA - CREAR SUPERUSUARIO EN RENDER"
echo "======================================================"
echo ""

# Navegar al directorio correcto
cd soptraloc_system

echo "1️⃣  Verificando usuarios existentes..."
python manage.py shell --settings=config.settings_production <<'EOF'
from django.contrib.auth.models import User

print(f"\nTotal usuarios en base de datos: {User.objects.count()}")

if User.objects.count() > 0:
    print("\nUsuarios existentes:")
    for user in User.objects.all():
        print(f"  - Username: {user.username}")
        print(f"    Email: {user.email}")
        print(f"    is_superuser: {user.is_superuser}")
        print(f"    is_staff: {user.is_staff}")
        print(f"    is_active: {user.is_active}")
        print()
else:
    print("\n⚠️  NO HAY USUARIOS - Necesitas crear uno")
EOF

echo ""
echo "======================================================"
echo "2️⃣  CREANDO SUPERUSUARIO AHORA..."
echo "======================================================"
echo ""

# Crear superusuario forzadamente
python manage.py shell --settings=config.settings_production <<'EOF'
from django.contrib.auth.models import User
import sys

# Eliminar usuario admin si existe (para empezar limpio)
if User.objects.filter(username='admin').exists():
    print("⚠️  Usuario 'admin' existe, eliminándolo para recrear...")
    User.objects.filter(username='admin').delete()
    print("✅ Usuario eliminado")

# Crear superusuario nuevo
print("\n🆕 Creando superusuario 'admin'...")
try:
    user = User.objects.create_superuser(
        username='admin',
        email='admin@soptraloc.com',
        password='1234'
    )
    print("✅ SUPERUSUARIO CREADO EXITOSAMENTE")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   is_superuser: {user.is_superuser}")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_active: {user.is_active}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
EOF

echo ""
echo "======================================================"
echo "3️⃣  VERIFICANDO AUTENTICACIÓN..."
echo "======================================================"
echo ""

python manage.py shell --settings=config.settings_production <<'EOF'
from django.contrib.auth import authenticate

print("Probando autenticación con admin/1234...")
user = authenticate(username='admin', password='1234')

if user:
    print("✅ AUTENTICACIÓN EXITOSA")
    print(f"   Usuario autenticado: {user.username}")
    print(f"   ID: {user.id}")
else:
    print("❌ AUTENTICACIÓN FALLÓ")
    print("   Esto NO debería ocurrir")
EOF

echo ""
echo "======================================================"
echo "✅ PROCESO COMPLETADO"
echo "======================================================"
echo ""
echo "Ahora intenta acceder a:"
echo "  https://soptraloc.onrender.com/admin/"
echo ""
echo "Credenciales:"
echo "  Usuario: admin"
echo "  Password: 1234"
echo ""
echo "======================================================"
