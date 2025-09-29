#!/bin/bash

# SafaryLoc - Deploy Completo en DigitalOcean
# Ejecutar como root en tu droplet Ubuntu

set -e

echo "🌊 Iniciando deploy de SafaryLoc en DigitalOcean..."
echo "⏰ Tiempo estimado: 5-10 minutos"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Actualizar sistema
print_status "Actualizando sistema Ubuntu..."
apt update && apt upgrade -y

# 2. Instalar dependencias
print_status "Instalando dependencias del sistema..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    postgresql \
    postgresql-contrib \
    git \
    curl \
    wget \
    htop \
    ufw \
    build-essential \
    libpq-dev

print_success "Dependencias instaladas correctamente"

# 3. Crear usuario de aplicación
print_status "Creando usuario de aplicación..."
useradd --system --shell /bin/bash --home /opt/safary --create-home safary || true
print_success "Usuario 'safary' creado"

# 4. Clonar repositorio
print_status "Clonando repositorio desde GitHub..."
cd /opt/safary
if [ -d "soptraloc" ]; then
    rm -rf soptraloc
fi

git clone https://github.com/Safary16/soptraloc.git
chown -R safary:safary soptraloc
cd soptraloc

print_success "Repositorio clonado correctamente"

# 5. Configurar entorno virtual Python
print_status "Configurando entorno virtual Python..."
sudo -u safary python3 -m venv venv
sudo -u safary /opt/safary/soptraloc/venv/bin/pip install --upgrade pip
sudo -u safary /opt/safary/soptraloc/venv/bin/pip install -r requirements.txt

print_success "Entorno virtual configurado"

# 6. Configurar PostgreSQL
print_status "Configurando base de datos PostgreSQL..."
sudo -u postgres createuser --createdb --login --superuser safary || true
sudo -u postgres createdb safarylocdb --owner=safary || true
sudo -u postgres psql -c "ALTER USER safary PASSWORD 'SafaryLoc2025!Secure';" || true

print_success "PostgreSQL configurado"

# 7. Crear archivo de configuración de producción
print_status "Creando configuración de producción..."
SERVER_IP=$(curl -s http://checkip.amazonaws.com || curl -s http://ipinfo.io/ip || hostname -I | awk '{print $1}')

sudo -u safary tee /opt/safary/soptraloc/.env << EOF
DEBUG=False
SECRET_KEY=safary-super-secret-production-key-$(openssl rand -hex 16)
DATABASE_URL=postgresql://safary:SafaryLoc2025!Secure@localhost:5432/safarylocdb
ALLOWED_HOSTS=${SERVER_IP},localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings_production
STATIC_ROOT=/opt/safary/soptraloc/soptraloc_system/staticfiles
MEDIA_ROOT=/opt/safary/soptraloc/soptraloc_system/media
EOF

print_success "Configuración de producción creada"

# 8. Ejecutar migraciones y setup inicial
print_status "Ejecutando migraciones de Django..."
cd soptraloc_system

# Configurar Django
sudo -u safary /opt/safary/soptraloc/venv/bin/python manage.py migrate --settings=config.settings_production
sudo -u safary /opt/safary/soptraloc/venv/bin/python manage.py collectstatic --noinput --settings=config.settings_production

# Crear directorios necesarios
mkdir -p staticfiles media
chown -R safary:safary staticfiles media

print_success "Migraciones ejecutadas"

# 9. Crear superusuario
print_status "Creando superusuario..."
sudo -u safary /opt/safary/soptraloc/venv/bin/python manage.py shell --settings=config.settings_production << EOF
from django.contrib.auth.models import User
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@safary.com', 'admin123')
    print('✅ Superusuario creado: admin/admin123')
else:
    print('✅ Superusuario ya existe')
EOF

print_success "Superusuario configurado"

# 10. Verificar datos de contenedores
print_status "Verificando datos de contenedores..."
CONTAINER_COUNT=$(sudo -u safary /opt/safary/soptraloc/venv/bin/python manage.py shell --settings=config.settings_production -c "
from apps.containers.models import Container
print(Container.objects.count())
" 2>/dev/null)

if [ "$CONTAINER_COUNT" -gt 0 ]; then
    print_success "$CONTAINER_COUNT contenedores disponibles en la base de datos"
else
    print_warning "No hay contenedores en la base de datos, pero la aplicación funcionará"
fi

# 11. Configurar Gunicorn como servicio systemd
print_status "Configurando servicio Gunicorn..."
tee /etc/systemd/system/safary.service << EOF
[Unit]
Description=SafaryLoc Django Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=safary
Group=safary
WorkingDirectory=/opt/safary/soptraloc/soptraloc_system
Environment="PATH=/opt/safary/soptraloc/venv/bin"
EnvironmentFile=/opt/safary/soptraloc/.env
ExecStart=/opt/safary/soptraloc/venv/bin/gunicorn --workers 3 --timeout 120 --bind unix:/opt/safary/soptraloc/safary.sock config.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

print_success "Servicio Gunicorn configurado"

# 12. Configurar Nginx
print_status "Configurando servidor web Nginx..."
tee /etc/nginx/sites-available/safary << EOF
server {
    listen 80;
    server_name ${SERVER_IP} localhost;

    client_max_body_size 50M;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias /opt/safary/soptraloc/soptraloc_system/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /opt/safary/soptraloc/soptraloc_system/media/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/safary/soptraloc/safary.sock;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF

# Activar configuración de Nginx
ln -sf /etc/nginx/sites-available/safary /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Validar configuración
nginx -t
if [ $? -ne 0 ]; then
    print_error "Error en configuración de Nginx"
    exit 1
fi

print_success "Nginx configurado correctamente"

# 13. Configurar firewall
print_status "Configurando firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

print_success "Firewall configurado"

# 14. Iniciar todos los servicios
print_status "Iniciando servicios..."
systemctl daemon-reload
systemctl enable postgresql
systemctl start postgresql
systemctl enable safary
systemctl start safary
systemctl enable nginx
systemctl restart nginx

# Esperar a que los servicios inicien
sleep 5

print_success "Servicios iniciados"

# 15. Verificar estado de servicios
print_status "Verificando estado de servicios..."

if systemctl is-active --quiet postgresql; then
    print_success "PostgreSQL: ✅ Activo"
else
    print_error "PostgreSQL: ❌ Inactivo"
fi

if systemctl is-active --quiet safary; then
    print_success "SafaryLoc App: ✅ Activo"
else
    print_error "SafaryLoc App: ❌ Inactivo"
    systemctl status safary --no-pager -l
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx: ✅ Activo"
else
    print_error "Nginx: ❌ Inactivo"
fi

# 16. Prueba final
print_status "Realizando prueba de conectividad..."
sleep 3

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    print_success "Aplicación responde correctamente (HTTP $HTTP_CODE)"
else
    print_warning "La aplicación no responde como se esperaba (HTTP $HTTP_CODE)"
    print_status "Revisando logs..."
    systemctl status safary --no-pager -l | tail -10
fi

# 17. Información final
echo ""
echo "🎉 ¡Deploy completado!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 URLS DE ACCESO:"
echo "   Dashboard:    http://${SERVER_IP}/"
echo "   Dashboard:    http://${SERVER_IP}/dashboard/"
echo "   Admin Panel:  http://${SERVER_IP}/admin/"
echo "   API Docs:     http://${SERVER_IP}/swagger/"
echo ""
echo "🔐 CREDENCIALES:"
echo "   Usuario:      admin"
echo "   Contraseña:   admin123"
echo ""
echo "📱 ACCESO MÓVIL:"
echo "   Desde cualquier smartphone, tablet o PC"
echo "   Solo navega a: http://${SERVER_IP}/"
echo ""
echo "🔧 COMANDOS ÚTILES:"
echo "   Ver logs:        sudo journalctl -u safary -f"
echo "   Reiniciar app:   sudo systemctl restart safary"
echo "   Estado servicios: sudo systemctl status safary nginx postgresql"
echo ""
echo "💰 COSTO:"
echo "   Con GitHub Student Pack: $4/mes = 50 meses GRATIS"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "¡Tu sistema logístico está listo para usar desde cualquier dispositivo!"