#!/usr/bin/env bash
# Build script para Render.com - SoptraLoc TMS
set -o errexit

echo "=========================================="
echo "🚀 SOPTRALOC TMS - BUILD"
echo "=========================================="

# 1. Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# 2. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 3. Colectar archivos estáticos
echo " Colectando archivos estáticos..."
python manage.py collectstatic --no-input

# 4. Ejecutar migraciones con el nuevo comando seguro
echo "🔄 Ejecutando migraciones..."
python manage.py render_migrate

# 5. Crear superusuario admin
echo "👤 Creando superusuario admin..."
python manage.py reset_admin --username=admin --password=1234

# 6. Iniciar Gunicorn
echo "🚀 Iniciando Gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

echo "=========================================="
echo "✅ Build completado exitosamente"
echo "=========================================="
