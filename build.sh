#!/usr/bin/env bash
# Build script optimizado para Render.com - SoptraLoc TMS v3.0
# Deploy desde CERO
set -o errexit

echo "=========================================================================="
echo "🚀 BUILD SOPTRALOC TMS v3.0 - RENDER.COM"
echo "=========================================================================="
echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip setuptools wheel

# Instalar dependencias de producción
echo "📦 Instalando dependencias de producción..."
pip install -r requirements.txt

# Verificar instalación de paquetes críticos
echo "🔍 Verificando paquetes críticos..."
python -c "import django; print(f'✅ Django {django.get_version()}')"
python -c "import psycopg2; print('✅ psycopg2 instalado')"
python -c "import whitenoise; print('✅ whitenoise instalado')"
python -c "import gunicorn; print('✅ gunicorn instalado')"

# Navegar al directorio del proyecto
cd soptraloc_system

# Crear directorio de logs si no existe
mkdir -p logs

# Aplicar migraciones de base de datos
echo "🔄 Aplicando migraciones de base de datos..."
python manage.py migrate --settings=config.settings_production --noinput

# Recopilar archivos estáticos con compresión
echo "📁 Recopilando y comprimiendo archivos estáticos..."
python manage.py collectstatic --noinput --clear --settings=config.settings_production

# Verificar archivos críticos
echo "🔍 Verificando archivos estáticos críticos..."
if [ -f "staticfiles/js/realtime-clock.js" ]; then
    echo "✅ realtime-clock.js encontrado"
else
    echo "⚠️  ADVERTENCIA: realtime-clock.js no encontrado"
fi

echo ""
echo "=========================================================================="
echo "✅ BUILD COMPLETADO EXITOSAMENTE"
echo "=========================================================================="
echo "Sistema: SoptraLoc TMS v3.0"
echo "Features: Reloj ATC + ML Routing + Alertas"
echo "Apps: routing, containers, drivers, warehouses, core"
echo "Deploy: Desde CERO - Optimizado"
echo "=========================================================================="
