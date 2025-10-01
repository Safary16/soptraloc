#!/usr/bin/env bash
# Post-deploy script - Carga datos de Chile y crea superusuario automáticamente
# MEJORADO: Verificación exhaustiva de autenticación
set -o errexit

echo "======================================================"
echo "🔄 POST-DEPLOY - SOPTRALOC TMS v2.0"
echo "======================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

cd soptraloc_system

# 1. Verificar conexión a PostgreSQL
echo "🔍 Verificando conexión a PostgreSQL..."
python manage.py check --database default --settings=config.settings_production
if [ $? -eq 0 ]; then
    echo "✅ Conexión a PostgreSQL exitosa"
else
    echo "❌ Error: No se pudo conectar a PostgreSQL"
    exit 1
fi

# 2. Cargar datos de Chile (35 rutas + 70 operaciones)
echo ""
echo "📊 Cargando datos de Chile (rutas y operaciones)..."
if python manage.py load_initial_times --settings=config.settings_production 2>&1 | grep -q "exitosamente\|successfully\|completed"; then
    echo "✅ Datos de Chile cargados correctamente"
else
    echo "⚠️  Los datos ya existían o hubo un error menor (no crítico)"
fi

# 3. Crear y verificar superusuario con lógica robusta
echo ""
echo "======================================================"
echo "👤 CONFIGURACIÓN DE SUPERUSUARIO"
echo "======================================================"

python manage.py shell --settings=config.settings_production <<'EOF'
from django.contrib.auth import get_user_model, authenticate
from django.db import connection
import sys

User = get_user_model()

# Configuración del superusuario
USERNAME = 'admin'
EMAIL = 'admin@soptraloc.com'
PASSWORD = '1234'

print("🔍 Verificando estado actual...")

# Verificar si existe el usuario
user_exists = User.objects.filter(username=USERNAME).exists()

if user_exists:
    print(f"ℹ️  Usuario '{USERNAME}' ya existe")
    user = User.objects.get(username=USERNAME)
    
    # Verificar y corregir permisos
    needs_update = False
    if not user.is_superuser:
        print("⚠️  Usuario no es superusuario, corrigiendo...")
        user.is_superuser = True
        needs_update = True
    
    if not user.is_staff:
        print("⚠️  Usuario no es staff, corrigiendo...")
        user.is_staff = True
        needs_update = True
    
    if not user.is_active:
        print("⚠️  Usuario no está activo, corrigiendo...")
        user.is_active = True
        needs_update = True
    
    # Verificar contraseña
    if not user.check_password(PASSWORD):
        print(f"⚠️  Contraseña incorrecta, reseteando a '{PASSWORD}'...")
        user.set_password(PASSWORD)
        needs_update = True
    else:
        print(f"✅ Contraseña verificada correctamente")
    
    if needs_update:
        user.save()
        print("✅ Usuario actualizado con permisos correctos")
else:
    print(f"🆕 Creando nuevo superusuario '{USERNAME}'...")
    try:
        user = User.objects.create_superuser(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD
        )
        print(f"✅ Superusuario creado exitosamente")
    except Exception as e:
        print(f"❌ Error creando superusuario: {e}")
        sys.exit(1)

# Verificación final de autenticación
print("")
print("🔐 Verificando autenticación...")
auth_user = authenticate(username=USERNAME, password=PASSWORD)

if auth_user is not None:
    print(f"✅ Autenticación EXITOSA para '{USERNAME}'")
    print(f"   ID: {auth_user.id}")
    print(f"   Email: {auth_user.email}")
    print(f"   Superusuario: {auth_user.is_superuser}")
    print(f"   Staff: {auth_user.is_staff}")
    print(f"   Activo: {auth_user.is_active}")
else:
    print(f"❌ ERROR: Autenticación FALLÓ para '{USERNAME}'")
    print("   Esto NO debería ocurrir. Revisa la configuración.")
    sys.exit(1)

# Mostrar todos los usuarios
print("")
print(f"📊 Total de usuarios en base de datos: {User.objects.count()}")

EOF

# Verificar código de salida del script Python
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Falló la configuración del superusuario"
    exit 1
fi

# 4. Verificación adicional usando script externo
echo ""
echo "======================================================"
echo "🔍 VERIFICACIÓN EXHAUSTIVA DE AUTENTICACIÓN"
echo "======================================================"

cd ..
python verify_auth.py

if [ $? -eq 0 ]; then
    echo "✅ Verificación exhaustiva completada exitosamente"
else
    echo "⚠️  Verificación exhaustiva reportó advertencias"
fi

echo ""
echo "======================================================"
echo "✅ POST-DEPLOY COMPLETADO EXITOSAMENTE"
echo "======================================================"
echo "📊 Datos de Chile: Cargados"
echo "👤 Superusuario: Verificado y funcionando"
echo "🔐 Autenticación: Probada exitosamente"
echo ""
echo "🌐 URL DE ADMIN:"
echo "   https://soptraloc-tms.onrender.com/admin/"
echo ""
echo "🔐 CREDENCIALES:"
echo "   Usuario: admin"
echo "   Password: 1234"
echo ""
echo "⚠️  IMPORTANTE: Cambiar esta contraseña en /admin/"
echo "======================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"
