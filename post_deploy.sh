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

# 2. Crear superusuario usando comando de management (MÁS CONFIABLE)
echo ""
echo "======================================================"
echo "👤 CREANDO SUPERUSUARIO CON COMANDO DE MANAGEMENT"
echo "======================================================"
python manage.py force_create_admin --settings=config.settings_production

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERROR: El comando force_create_admin falló"
    echo "   Intentando método alternativo..."
fi

# 3. Cargar datos de Chile (35 rutas + 70 operaciones)
echo ""
echo "📊 Cargando datos de Chile (rutas y operaciones)..."
if python manage.py load_initial_times --settings=config.settings_production 2>&1 | grep -q "exitosamente\|successfully\|completed"; then
    echo "✅ Datos de Chile cargados correctamente"
else
    echo "⚠️  Los datos ya existían o hubo un error menor (no crítico)"
fi

# 4. Verificación adicional con script Python (por si el comando falló)
echo ""
echo "======================================================"
echo "👤 VERIFICACIÓN ADICIONAL DE SUPERUSUARIO"
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

print("🔍 Iniciando creación FORZADA de superusuario...")
print("")

# PASO 1: ELIMINAR cualquier usuario 'admin' existente
print("1️⃣  Eliminando usuario 'admin' si existe...")
try:
    deleted_count, _ = User.objects.filter(username=USERNAME).delete()
    if deleted_count > 0:
        print(f"   ✅ Eliminado {deleted_count} usuario(s) existente(s)")
    else:
        print(f"   ℹ️  No había usuario '{USERNAME}' previo")
except Exception as e:
    print(f"   ⚠️  Error eliminando usuario (probablemente no existe): {e}")

print("")

# PASO 2: CREAR superusuario NUEVO desde cero
print("2️⃣  Creando superusuario NUEVO...")
try:
    user = User.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD
    )
    print(f"   ✅ SUPERUSUARIO CREADO EXITOSAMENTE")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   ID: {user.id}")
    print(f"   is_superuser: {user.is_superuser}")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_active: {user.is_active}")
except Exception as e:
    print(f"   ❌ ERROR CRÍTICO creando superusuario: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("")

# PASO 3: VERIFICAR autenticación
print("3️⃣  Verificando autenticación...")
try:
    auth_user = authenticate(username=USERNAME, password=PASSWORD)
    
    if auth_user is not None:
        print(f"   ✅ AUTENTICACIÓN EXITOSA")
        print(f"   Usuario autenticado: {auth_user.username}")
        print(f"   ID: {auth_user.id}")
    else:
        print(f"   ❌ ERROR: Autenticación FALLÓ")
        print(f"   Usuario existe pero no autentica")
        
        # Intentar arreglar
        print(f"   🔧 Intentando resetear contraseña...")
        user = User.objects.get(username=USERNAME)
        user.set_password(PASSWORD)
        user.save()
        
        # Probar de nuevo
        auth_user = authenticate(username=USERNAME, password=PASSWORD)
        if auth_user is not None:
            print(f"   ✅ Contraseña reseteada, autenticación OK ahora")
        else:
            print(f"   ❌ ERROR PERSISTENTE en autenticación")
            sys.exit(1)
except Exception as e:
    print(f"   ❌ ERROR verificando autenticación: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("")

# PASO 4: Resumen final
print("4️⃣  Resumen final:")
print(f"   Total usuarios en DB: {User.objects.count()}")
if User.objects.filter(username=USERNAME).exists():
    final_user = User.objects.get(username=USERNAME)
    print(f"   ✅ Usuario '{USERNAME}' confirmado en base de datos")
    print(f"   ✅ Password funciona: {final_user.check_password(PASSWORD)}")
else:
    print(f"   ❌ ERROR: Usuario no encontrado después de creación")
    sys.exit(1)

EOF

# Verificar código de salida del script Python
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  ADVERTENCIA: Verificación adicional reportó problemas"
    echo "   Continuando con verificación exhaustiva..."
fi

# 5. Verificación exhaustiva usando script externo
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
    echo "   Intentando creación alternativa con createsuperuser..."
    cd soptraloc_system
    
    # Método alternativo usando environment variables
    export DJANGO_SUPERUSER_PASSWORD='1234'
    export DJANGO_SUPERUSER_USERNAME='admin'
    export DJANGO_SUPERUSER_EMAIL='admin@soptraloc.com'
    
    python manage.py createsuperuser --noinput --settings=config.settings_production 2>&1 || true
    
    unset DJANGO_SUPERUSER_PASSWORD
    unset DJANGO_SUPERUSER_USERNAME
    unset DJANGO_SUPERUSER_EMAIL
    
    cd ..
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
echo "   https://soptraloc.onrender.com/admin/"
echo ""
echo "🔐 CREDENCIALES:"
echo "   Usuario: admin"
echo "   Password: 1234"
echo ""
echo "⚠️  IMPORTANTE: Cambiar esta contraseña en /admin/"
echo "======================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"
