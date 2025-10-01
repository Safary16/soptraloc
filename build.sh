#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Iniciando build de SoptraLoc para Render..."

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Navegar al directorio del proyecto
cd soptraloc_system

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --settings=config.settings_production

echo "✅ Build completado exitosamente!"
