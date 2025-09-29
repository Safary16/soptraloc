#!/bin/bash

# Azure App Service startup script
echo "🚀 Iniciando SafaryLoc en Azure..."

# Cambiar al directorio de la aplicación
cd /home/site/wwwroot/soptraloc_system

# Instalar dependencias si no están
if [ ! -d "/home/site/wwwroot/venv" ]; then
    echo "📦 Instalando dependencias..."
    python -m venv /home/site/wwwroot/venv
    source /home/site/wwwroot/venv/bin/activate
    pip install -r /home/site/wwwroot/requirements.txt
fi

# Activar entorno virtual
source /home/site/wwwroot/venv/bin/activate

# Ejecutar migraciones
echo "📊 Ejecutando migraciones..."
python manage.py migrate --settings=config.settings_production --noinput

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --settings=config.settings_production --noinput

# Crear superusuario si no existe
echo "👤 Configurando superusuario..."
python manage.py shell --settings=config.settings_production << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@safary.com', 'admin123')
    print('✅ Superusuario creado')
EOF

# Iniciar Gunicorn
echo "🌐 Iniciando servidor web..."
exec gunicorn --bind=0.0.0.0:$PORT --timeout 600 --workers 2 config.wsgi:application