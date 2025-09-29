#!/bin/bash

# Script de deploy automático para DigitalOcean
echo "🌊 Configurando SafaryLoc en DigitalOcean..."

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git curl

# Crear usuario de la aplicación
sudo useradd --system --shell /bin/bash --home /opt/safary --create-home safary

# Clonar repositorio
cd /opt/safary
sudo git clone https://github.com/Safary16/soptraloc.git
sudo chown -R safary:safary soptraloc
cd soptraloc

# Crear entorno virtual
sudo -u safary python3 -m venv venv
sudo -u safary /opt/safary/soptraloc/venv/bin/pip install -r requirements.txt

# Configurar PostgreSQL
sudo -u postgres createuser --superuser safary
sudo -u postgres createdb safarylocdb
sudo -u postgres psql -c "ALTER USER safary PASSWORD 'SafaryLoc2025!';"

# Variables de entorno
sudo -u safary tee /opt/safary/soptraloc/.env << EOF
DEBUG=False
SECRET_KEY=safary-super-secret-key-production-2025
DATABASE_URL=postgresql://safary:SafaryLoc2025!@localhost:5432/safarylocdb
ALLOWED_HOSTS=*
DJANGO_SETTINGS_MODULE=config.settings_production
EOF

# Ejecutar migraciones
cd soptraloc_system
sudo -u safary /opt/safary/soptraloc/venv/bin/python manage.py migrate
sudo -u safary /opt/safary/soptraloc/venv/bin/python manage.py collectstatic --noinput

# Crear superusuario
sudo -u safary /opt/safary/soptraloc/venv/bin/python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@safary.com', 'admin123')
    print('✅ Superusuario creado')
"

# Configurar Gunicorn como servicio
sudo tee /etc/systemd/system/safary.service << EOF
[Unit]
Description=SafaryLoc Django Application
After=network.target

[Service]
User=safary
Group=safary
WorkingDirectory=/opt/safary/soptraloc/soptraloc_system
Environment="PATH=/opt/safary/soptraloc/venv/bin"
EnvironmentFile=/opt/safary/soptraloc/.env
ExecStart=/opt/safary/soptraloc/venv/bin/gunicorn --workers 3 --bind unix:/opt/safary/soptraloc/safary.sock config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configurar Nginx
sudo tee /etc/nginx/sites-available/safary << EOF
server {
    listen 80;
    server_name _;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /opt/safary/soptraloc/soptraloc_system;
    }

    location /media/ {
        root /opt/safary/soptraloc/soptraloc_system;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/safary/soptraloc/safary.sock;
    }
}
EOF

# Activar configuración
sudo ln -sf /etc/nginx/sites-available/safary /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Iniciar servicios
sudo systemctl daemon-reload
sudo systemctl enable safary
sudo systemctl start safary
sudo systemctl enable nginx
sudo systemctl restart nginx

# Configurar firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "✅ SafaryLoc instalado exitosamente!"
echo "🌐 Accede en: http://TU_IP_PUBLICA/"
echo "⚙️ Admin: http://TU_IP_PUBLICA/admin/"
echo "📊 Dashboard: http://TU_IP_PUBLICA/dashboard/"
echo ""
echo "🔐 Credenciales:"
echo "Usuario: admin"
echo "Contraseña: admin123"