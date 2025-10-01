#!/usr/bin/env bash
# Script de diagnóstico rápido para ejecutar en Render Shell
# Uso: bash debug_render.sh

echo "======================================================"
echo "🔍 DIAGNÓSTICO RÁPIDO - SOPTRALOC TMS"
echo "======================================================"
echo ""

cd soptraloc_system

echo "1️⃣  Verificando variables de entorno..."
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-'No configurado'}"
echo "DATABASE_URL: ${DATABASE_URL:0:30}... (truncado)"
echo ""

echo "2️⃣  Verificando conexión a base de datos..."
python manage.py check --database default --settings=config.settings_production 2>&1 | head -20
echo ""

echo "3️⃣  Verificando usuarios..."
python manage.py shell --settings=config.settings_production <<'EOF'
from django.contrib.auth.models import User

total = User.objects.count()
print(f"Total usuarios: {total}")

if total > 0:
    print("\nUsuarios existentes:")
    for user in User.objects.all():
        print(f"  - {user.username}")
        print(f"    Superusuario: {user.is_superuser}")
        print(f"    Staff: {user.is_staff}")
        print(f"    Activo: {user.is_active}")
else:
    print("\n⚠️  NO HAY USUARIOS EN LA BASE DE DATOS")
EOF
echo ""

echo "4️⃣  Probando autenticación con admin/1234..."
python manage.py shell --settings=config.settings_production <<'EOF'
from django.contrib.auth import authenticate

user = authenticate(username='admin', password='1234')

if user:
    print("✅ Autenticación EXITOSA")
    print(f"   Usuario: {user.username}")
    print(f"   ID: {user.id}")
else:
    print("❌ Autenticación FALLÓ")
    print("   Las credenciales son incorrectas o el usuario no existe")
EOF
echo ""

echo "======================================================"
echo "✅ DIAGNÓSTICO COMPLETADO"
echo "======================================================"
echo ""
echo "Si la autenticación falló:"
echo "1. Ejecuta: python manage.py createsuperuser --settings=config.settings_production"
echo "2. O ejecuta: python ../verify_auth.py"
echo ""
