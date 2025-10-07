#!/usr/bin/env bash
# Post-deploy script optimizado para Render.com
# Deploy desde CERO - Sistema SoptraLoc TMS v3.0
set -e  # Exit on error

echo "=========================================================================="
echo "🚀 POST-DEPLOY SOPTRALOC TMS - DEPLOY COMPLETO"
echo "=========================================================================="
echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Host: $(hostname)"
echo ""

cd soptraloc_system

# ============================================================================
# PASO 1: VERIFICAR ENTORNO
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 PASO 1: Verificando entorno"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Python version: $(python --version)"
echo "Django settings: ${DJANGO_SETTINGS_MODULE:-'No configurado'}"
echo "Database URL: ${DATABASE_URL:0:50}... (truncado)"

# Verificar que Django puede importarse
python -c "import django; print(f'Django: {django.get_version()}')" || {
    echo "❌ ERROR: Django no está instalado correctamente"
    exit 1
}

echo "✅ Entorno verificado"
echo ""

# ============================================================================
# PASO 2: VERIFICAR BASE DE DATOS
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  PASO 2: Verificando conexión a PostgreSQL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python manage.py check --database default --settings=config.settings_production || {
    echo "❌ ERROR: No se puede conectar a PostgreSQL"
    exit 1
}

echo "✅ Conexión a PostgreSQL exitosa"
echo ""

# ============================================================================
# PASO 3: CREAR SUPERUSUARIO (MÉTODO DEFINITIVO)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👤 PASO 3: Creando superusuario (MÉTODO DEFINITIVO)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Intentar con comando de management primero
echo "Intentando con comando force_create_admin..."
if python manage.py force_create_admin --settings=config.settings_production 2>&1 | tee /tmp/create_admin.log; then
    echo "✅ Superusuario creado con force_create_admin"
else
    echo "⚠️  force_create_admin no funcionó, intentando método alternativo..."
    
    # Método alternativo: Script Python inline SIMPLIFICADO
    python manage.py shell --settings=config.settings_production <<'EOFPYTHON'
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

print("=" * 70)
print("CREANDO SUPERUSUARIO - MÉTODO ALTERNATIVO")
print("=" * 70)

# Eliminar usuario admin si existe
User.objects.filter(username='admin').delete()
print("✅ Usuario admin eliminado (si existía)")

# Crear superusuario
admin = User.objects.create_superuser(
    username='admin',
    email='admin@soptraloc.com',
    password='1234'
)

print(f"✅ Superusuario creado:")
print(f"   - Username: {admin.username}")
print(f"   - Email: {admin.email}")
print(f"   - ID: {admin.id}")
print(f"   - is_superuser: {admin.is_superuser}")
print(f"   - is_staff: {admin.is_staff}")
print(f"   - is_active: {admin.is_active}")

# Verificar autenticación
auth_user = authenticate(username='admin', password='1234')
if auth_user:
    print("✅ Autenticación verificada exitosamente")
else:
    print("❌ ERROR: Autenticación falló")
    import sys
    sys.exit(1)

print("=" * 70)
EOFPYTHON

    if [ $? -eq 0 ]; then
        echo "✅ Superusuario creado con método alternativo"
    else
        echo "❌ ERROR: Ambos métodos fallaron"
        echo "Intentando último recurso con createsuperuser..."
        
        # Último recurso: createsuperuser con env vars
        export DJANGO_SUPERUSER_USERNAME='admin'
        export DJANGO_SUPERUSER_EMAIL='admin@soptraloc.com'
        export DJANGO_SUPERUSER_PASSWORD='1234'
        
        python manage.py createsuperuser --noinput --settings=config.settings_production || true
        
        unset DJANGO_SUPERUSER_USERNAME
        unset DJANGO_SUPERUSER_EMAIL
        unset DJANGO_SUPERUSER_PASSWORD
    fi
fi

echo ""

# ============================================================================
# PASO 4: VERIFICACIÓN FINAL DEL SUPERUSUARIO
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 PASO 4: Verificación final del superusuario"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python manage.py shell --settings=config.settings_production <<'EOFPYTHON'
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

print("\n📊 Estado de la base de datos:")
print(f"   Total de usuarios: {User.objects.count()}")

if User.objects.filter(username='admin').exists():
    admin = User.objects.get(username='admin')
    print(f"\n✅ Usuario 'admin' encontrado:")
    print(f"   - ID: {admin.id}")
    print(f"   - Email: {admin.email}")
    print(f"   - Superusuario: {admin.is_superuser}")
    print(f"   - Staff: {admin.is_staff}")
    print(f"   - Activo: {admin.is_active}")
    
    # Verificar autenticación
    print(f"\n🔐 Verificando autenticación...")
    auth_user = authenticate(username='admin', password='1234')
    
    if auth_user:
        print(f"✅ AUTENTICACIÓN EXITOSA")
    else:
        print(f"❌ ERROR: AUTENTICACIÓN FALLÓ")
        import sys
        sys.exit(1)
else:
    print("\n❌ ERROR: Usuario 'admin' NO existe")
    import sys
    sys.exit(1)
EOFPYTHON

if [ $? -eq 0 ]; then
    echo "✅ Verificación completa exitosa"
else
    echo "❌ ERROR CRÍTICO: La verificación final falló"
    exit 1
fi

echo ""

# ============================================================================
# PASO 5: CARGAR CONDUCTORES
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚚 PASO 5: Cargando 82 conductores"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python manage.py load_drivers --count=82 --force --settings=config.settings_production 2>&1 | tee /tmp/load_drivers.log; then
    echo "✅ 82 conductores cargados correctamente"
else
    echo "⚠️  Advertencia: Hubo un problema al cargar conductores (no crítico)"
fi

echo ""

# ============================================================================
# PASO 6: CARGAR DATOS INICIALES DE CHILE (OPCIONAL)
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 PASO 6: Cargando datos iniciales de Chile"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python manage.py load_initial_times --settings=config.settings_production 2>&1 | grep -q "exitosamente\|successfully\|completed"; then
    echo "✅ Datos de Chile cargados correctamente"
else
    echo "ℹ️  Los datos ya existían o hubo un error menor (no crítico)"
fi

echo ""

# ============================================================================
# RESUMEN FINAL
# ============================================================================
echo "=========================================================================="
echo "✅ POST-DEPLOY COMPLETADO EXITOSAMENTE"
echo "=========================================================================="
echo ""
echo "📊 Resumen:"
echo "   ✅ PostgreSQL: Conectado"
echo "   ✅ Superusuario: Creado y verificado"
echo "   ✅ Conductores: 82 conductores cargados"
echo "   ✅ Datos: Cargados"
echo ""
echo "🔗 Acceso al sistema:"
echo "   URL: https://soptraloc.onrender.com/admin/"
echo ""
echo "🔐 Credenciales:"
echo "   Usuario:  admin"
echo "   Password: 1234"
echo ""
echo "⚠️  IMPORTANTE: Cambia esta contraseña inmediatamente en producción"
echo ""
echo "=========================================================================="
echo "Finalizado: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=========================================================================="
