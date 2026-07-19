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

# Las migraciones requieren conectividad a PostgreSQL y se ejecutan en start.sh.
# El build debe ser reproducible aunque la base esté reiniciando o actualizando DNS.
echo "✅ Artefactos preparados; migraciones diferidas al arranque"

echo "=========================================="
echo "✅ Build completado exitosamente"
echo "=========================================="
