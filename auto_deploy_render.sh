#!/bin/bash
#
# Script de Deploy Automatizado a Render usando render.yaml
# ============================================================
# Este script prepara y despliega automáticamente el sistema SOPTRALOC a Render
#
# Uso:
#   chmod +x auto_deploy_render.sh
#   ./auto_deploy_render.sh
#

set -e  # Salir si hay algún error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funciones de utilidad
print_header() {
    echo -e "\n${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}${1}${NC}"
    echo -e "${BLUE}================================================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

print_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  ${1}${NC}"
}

# Función para generar SECRET_KEY
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(50))"
}

# Banner
clear
print_header "🚀 SOPTRALOC TMS - Deploy Automatizado a Render"

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "README.md" ] || [ ! -d "soptraloc_system" ]; then
    print_error "Debes ejecutar este script desde la raíz del proyecto"
    exit 1
fi

print_success "Directorio del proyecto verificado"

# 2. Verificar que Git está actualizado
print_info "Verificando estado de Git..."
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Hay cambios sin commitear"
    read -p "¿Quieres hacer commit y push ahora? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        git commit -m "chore: Preparar para deploy automatizado en Render"
        git push origin main
        print_success "Cambios commiteados y pusheados"
    fi
else
    print_success "Git está actualizado"
fi

# 3. Generar SECRET_KEY
print_info "Generando SECRET_KEY segura..."
SECRET_KEY=$(generate_secret_key)
print_success "SECRET_KEY generada: ${SECRET_KEY:0:20}..."

# 4. Configuración
MAPBOX_API_KEY="pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY200cTN6MGY5MGlqMDJpb2o5a3RvYTh2dSJ9.B0A7Nw0nDCXzjUBBN0i4aQ"

print_header "📝 Creando archivo render.yaml"

# 5. Crear render.yaml
cat > render.yaml << EOF
# Render Blueprint para SOPTRALOC TMS
# ====================================
# Este archivo configura automáticamente todos los servicios necesarios

databases:
  - name: soptraloc-db
    databaseName: soptraloc
    user: soptraloc_user
    plan: starter
    region: oregon

services:
  # PostgreSQL ya está definido arriba

  # Redis
  - type: redis
    name: soptraloc-redis
    plan: starter
    maxmemoryPolicy: allkeys-lru
    region: oregon
    ipAllowList: []

  # Web Service (Django)
  - type: web
    name: soptraloc-web
    runtime: python3
    region: oregon
    plan: starter
    branch: main
    buildCommand: pip install -r requirements.txt && python soptraloc_system/manage.py collectstatic --noinput && python soptraloc_system/manage.py migrate
    startCommand: cd soptraloc_system && gunicorn config.wsgi:application --bind 0.0.0.0:\$PORT --workers 3 --timeout 120
    healthCheckPath: /health/
    autoDeploy: true
    envVars:
      - key: SECRET_KEY
        sync: false
      - key: DEBUG
        value: False
      - key: MAPBOX_API_KEY
        value: ${MAPBOX_API_KEY}
      - key: DATABASE_URL
        fromDatabase:
          name: soptraloc-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: TIME_ZONE
        value: America/Santiago
      - key: PYTHONUNBUFFERED
        value: 1
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings
      - key: ALLOWED_HOSTS
        generateValue: true

  # Celery Worker
  - type: worker
    name: soptraloc-celery-worker
    runtime: python3
    region: oregon
    plan: starter
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: cd soptraloc_system && celery -A config worker -l info --concurrency=2
    autoDeploy: true
    envVars:
      - key: SECRET_KEY
        sync: false
      - key: DEBUG
        value: False
      - key: MAPBOX_API_KEY
        value: ${MAPBOX_API_KEY}
      - key: DATABASE_URL
        fromDatabase:
          name: soptraloc-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: TIME_ZONE
        value: America/Santiago
      - key: PYTHONUNBUFFERED
        value: 1
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings

  # Celery Beat
  - type: worker
    name: soptraloc-celery-beat
    runtime: python3
    region: oregon
    plan: starter
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: cd soptraloc_system && celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    autoDeploy: true
    envVars:
      - key: SECRET_KEY
        sync: false
      - key: DEBUG
        value: False
      - key: MAPBOX_API_KEY
        value: ${MAPBOX_API_KEY}
      - key: DATABASE_URL
        fromDatabase:
          name: soptraloc-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: redis
          name: soptraloc-redis
          property: connectionString
      - key: TIME_ZONE
        value: America/Santiago
      - key: PYTHONUNBUFFERED
        value: 1
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings
EOF

print_success "render.yaml creado exitosamente"

# 6. Crear archivo de variables de entorno para referencia
cat > .env.render << EOF
# Variables de entorno para Render
# =================================
# IMPORTANTE: Deberás agregar SECRET_KEY manualmente en Render Dashboard

SECRET_KEY=${SECRET_KEY}
DEBUG=False
MAPBOX_API_KEY=${MAPBOX_API_KEY}
TIME_ZONE=America/Santiago
PYTHONUNBUFFERED=1
DJANGO_SETTINGS_MODULE=config.settings

# Las siguientes se autoconfigura con render.yaml:
# DATABASE_URL (desde PostgreSQL)
# REDIS_URL (desde Redis)
# CELERY_BROKER_URL (desde Redis)
# CELERY_RESULT_BACKEND (desde Redis)
# ALLOWED_HOSTS (se genera automáticamente)
EOF

print_success ".env.render creado con tus variables"

# 7. Agregar a .gitignore
if ! grep -q ".env.render" .gitignore 2>/dev/null; then
    echo ".env.render" >> .gitignore
    print_success ".env.render agregado a .gitignore"
fi

# 8. Crear archivo de health check si no existe
if [ ! -f "soptraloc_system/config/urls.py" ]; then
    print_warning "Archivo urls.py no encontrado"
else
    print_info "Verificando endpoint /health/..."
    if ! grep -q "/health/" soptraloc_system/config/urls.py; then
        print_warning "No se encontró endpoint /health/ - Deberás agregarlo manualmente"
    else
        print_success "Endpoint /health/ verificado"
    fi
fi

# 9. Commit y push
print_header "📤 Preparando para commit y push"

git add render.yaml
git add .gitignore

if [ -n "$(git status --porcelain)" ]; then
    git commit -m "feat: Agregar render.yaml para deploy automatizado

- Configuración completa de todos los servicios
- PostgreSQL (plan starter)
- Redis (plan starter)
- Web Service (Django con gunicorn)
- Celery Worker (2 procesos)
- Celery Beat (scheduler)
- Variables de entorno configuradas
- Auto-deploy habilitado"
    
    print_success "Commit creado"
    
    print_info "Pusheando a GitHub..."
    git push origin main
    print_success "Push completado"
else
    print_info "No hay cambios para commitear"
fi

# 10. Guardar configuración
cat > render_deployment_info.json << EOF
{
  "deployment_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "repository": "https://github.com/Safary16/soptraloc",
  "branch": "main",
  "secret_key": "${SECRET_KEY}",
  "mapbox_api_key": "${MAPBOX_API_KEY}",
  "services": {
    "database": "soptraloc-db",
    "redis": "soptraloc-redis",
    "web": "soptraloc-web",
    "celery_worker": "soptraloc-celery-worker",
    "celery_beat": "soptraloc-celery-beat"
  },
  "regions": "oregon",
  "plans": "starter (free tier)"
}
EOF

print_success "Información de deploy guardada en render_deployment_info.json"

# 11. Instrucciones finales
print_header "✅ PREPARACIÓN COMPLETADA"

echo -e "${GREEN}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                    🎉 TODO LISTO PARA DEPLOY EN RENDER 🎉                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
${NC}"

echo -e "\n${CYAN}📋 PRÓXIMOS PASOS:${NC}\n"

echo -e "${YELLOW}1. Ve al Dashboard de Render:${NC}"
echo -e "   👉 https://dashboard.render.com/"

echo -e "\n${YELLOW}2. Haz clic en 'New' → 'Blueprint':${NC}"
echo -e "   - Connect your GitHub account (si no lo has hecho)"
echo -e "   - Selecciona el repositorio: Safary16/soptraloc"
echo -e "   - Render detectará automáticamente render.yaml"
echo -e "   - Haz clic en 'Apply'"

echo -e "\n${YELLOW}3. Configurar SECRET_KEY manualmente:${NC}"
echo -e "   - Una vez creados los servicios, ve a 'soptraloc-web'"
echo -e "   - Clic en 'Environment'"
echo -e "   - Busca 'SECRET_KEY' y actualiza su valor:"
echo -e "   ${GREEN}${SECRET_KEY}${NC}"

echo -e "\n${YELLOW}4. Espera a que se construyan los servicios (~5-10 min):${NC}"
echo -e "   ⏳ Database: soptraloc-db"
echo -e "   ⏳ Redis: soptraloc-redis"
echo -e "   ⏳ Web: soptraloc-web"
echo -e "   ⏳ Worker: soptraloc-celery-worker"
echo -e "   ⏳ Beat: soptraloc-celery-beat"

echo -e "\n${YELLOW}5. Una vez que 'soptraloc-web' esté 'Live':${NC}"
echo -e "   - Ve a 'soptraloc-web' → Shell"
echo -e "   - Ejecuta:"
echo -e "     ${GREEN}cd soptraloc_system${NC}"
echo -e "     ${GREEN}python manage.py createsuperuser${NC}"

echo -e "\n${YELLOW}6. (Opcional) Cargar datos de prueba:${NC}"
echo -e "   ${GREEN}python manage.py quick_test_data${NC}"

echo -e "\n${YELLOW}7. Verificar el sistema:${NC}"
echo -e "   ${GREEN}python test_system.py${NC}"

echo -e "\n${YELLOW}8. Acceder a tu aplicación:${NC}"
echo -e "   - Busca la URL en el Dashboard (soptraloc-web → URL)"
echo -e "   - Ejemplo: ${CYAN}https://soptraloc-web.onrender.com${NC}"
echo -e "   - Admin: ${CYAN}https://soptraloc-web.onrender.com/admin/${NC}"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📁 Archivos creados:${NC}"
echo -e "   ✅ render.yaml (configuración de servicios)"
echo -e "   ✅ .env.render (variables de entorno de referencia)"
echo -e "   ✅ render_deployment_info.json (información del deploy)"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${CYAN}💡 TIP: Guarda el archivo .env.render en un lugar seguro${NC}"
echo -e "${CYAN}   Contiene tu SECRET_KEY que necesitarás configurar en Render${NC}\n"

print_success "Script completado exitosamente!"
print_info "Para más información, consulta: RENDER_DEPLOYMENT_CHECKLIST.md"

echo ""
