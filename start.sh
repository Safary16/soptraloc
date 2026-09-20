#!/usr/bin/env bash
# Arranque seguro en Render: migra y arranca Gunicorn
set -o errexit
set -o nounset
set -o pipefail

echo "=========================================="
echo "🚀 SOPTRALOC TMS - ARRANQUE"
echo "=========================================="

echo "🗄️ Verificando/creando la base de datos..."
python manage.py ensure_database

echo "📦 Ejecutando migraciones de base de datos..."
python manage.py migrate --no-input

echo "👤 Asegurando usuario administrador..."
python manage.py ensure_admin

echo "🎨 Colectando archivos estáticos (garantiza whitenoise/estáticos vivos aunque el build no lo haga)..."
python manage.py collectstatic --no-input

echo "🌐 Iniciando Gunicorn..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}"
