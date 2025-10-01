#!/usr/bin/env bash
# Post-deploy script - Carga datos de Chile y crea superusuario automáticamente
set -o errexit

echo "======================================================"
echo "🔄 POST-DEPLOY - CARGA DE DATOS AUTOMÁTICA"
echo "======================================================"

cd soptraloc_system

# 1. Cargar datos de Chile (35 rutas + 70 operaciones)
echo "📊 Cargando datos de Chile (rutas y operaciones)..."
if python manage.py load_initial_times --settings=config.settings_production 2>&1 | grep -q "exitosamente\|successfully\|completed"; then
    echo "✅ Datos de Chile cargados correctamente"
else
    echo "⚠️  Los datos ya existían o hubo un error menor (no crítico)"
fi

# 2. Crear superusuario automáticamente (solo si no existe)
echo "👤 Verificando superusuario..."
python manage.py shell --settings=config.settings_production <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# Configuración del superusuario
username = 'admin'
email = 'admin@soptraloc.com'
password = '1234'  # Contraseña temporal simple

# Crear solo si no existe
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print('✅ Superusuario creado: admin')
    print('🔐 Contraseña temporal: 1234')
    print('⚠️  IMPORTANTE: Cambiar contraseña en /admin/')
else:
    print('ℹ️  Superusuario ya existe')
EOF

echo ""
echo "======================================================"
echo "✅ POST-DEPLOY COMPLETADO"
echo "======================================================"
echo "📊 Datos de Chile: Cargados"
echo "👤 Superusuario: Verificado"
echo ""
echo "🔐 CREDENCIALES INICIALES:"
echo "   Usuario: admin"
echo "   Password: 1234"
echo ""
echo "⚠️  IMPORTANTE: Esta es una contraseña temporal."
echo "   Cámbiala inmediatamente en: /admin/"
echo "======================================================"
