#!/bin/bash

# Deploy script for Railway
echo "🚀 Iniciando deploy en Railway..."

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate --noinput

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario si no existe
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@soptraloc.com', 'admin123')
    print('✅ Superusuario creado: admin/admin123')
"

echo "✅ Deploy completado!"