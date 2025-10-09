#!/bin/bash
#
# Script para iniciar todos los servicios de SOPTRALOC TMS
# Uso: ./start_services.sh
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "======================================================================="
echo "  🚀 INICIANDO SOPTRALOC TMS"
echo "======================================================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para verificar si un proceso está corriendo
check_process() {
    if pgrep -f "$1" > /dev/null; then
        echo -e "${GREEN}✅ $2 está corriendo${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $2 no está corriendo${NC}"
        return 1
    fi
}

# 1. Verificar/Iniciar Redis
echo "1️⃣  Verificando Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis ya está corriendo${NC}"
else
    echo "   Iniciando Redis..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis iniciado correctamente${NC}"
    else
        echo -e "${RED}❌ Error al iniciar Redis${NC}"
        exit 1
    fi
fi
echo ""

# 2. Activar virtualenv
echo "2️⃣  Activando virtualenv..."
if [ -f "/workspaces/soptraloc/venv/bin/activate" ]; then
    source /workspaces/soptraloc/venv/bin/activate
    echo -e "${GREEN}✅ Virtualenv activado${NC}"
else
    echo -e "${RED}❌ No se encontró virtualenv en /workspaces/soptraloc/venv${NC}"
    exit 1
fi
echo ""

# 3. Verificar/Iniciar Celery Worker
echo "3️⃣  Verificando Celery Worker..."
if check_process "celery.*worker" "Celery Worker"; then
    echo "   Celery Worker ya está activo"
else
    echo "   Iniciando Celery Worker..."
    nohup celery -A config worker --loglevel=info > /tmp/celery_worker.log 2>&1 &
    sleep 3
    if check_process "celery.*worker" "Celery Worker"; then
        echo -e "${GREEN}✅ Celery Worker iniciado${NC}"
    else
        echo -e "${RED}❌ Error al iniciar Celery Worker${NC}"
        echo "   Ver logs en: /tmp/celery_worker.log"
    fi
fi
echo ""

# 4. Verificar/Iniciar Celery Beat
echo "4️⃣  Verificando Celery Beat..."
if check_process "celery.*beat" "Celery Beat"; then
    echo "   Celery Beat ya está activo"
else
    echo "   Iniciando Celery Beat..."
    nohup celery -A config beat --loglevel=info > /tmp/celery_beat.log 2>&1 &
    sleep 3
    if check_process "celery.*beat" "Celery Beat"; then
        echo -e "${GREEN}✅ Celery Beat iniciado${NC}"
    else
        echo -e "${RED}❌ Error al iniciar Celery Beat${NC}"
        echo "   Ver logs en: /tmp/celery_beat.log"
    fi
fi
echo ""

# 5. Estado del sistema
echo "5️⃣  Verificando estado del sistema..."
echo ""
python manage.py shell -c "
from apps.containers.models import Container
from apps.drivers.models import Assignment, Location, Driver
print('📊 ESTADO DEL SISTEMA:')
print(f'  📦 Contenedores: {Container.objects.count()}')
print(f'  👥 Asignaciones: {Assignment.objects.count()}')
print(f'  📍 Ubicaciones: {Location.objects.count()}')
print(f'  🚗 Conductores: {Driver.objects.count()}')
"
echo ""

echo "======================================================================="
echo -e "  ${GREEN}✅ SOPTRALOC TMS INICIADO CORRECTAMENTE${NC}"
echo "======================================================================="
echo ""
echo "📝 Comandos útiles:"
echo "   - Ver logs Worker: tail -f /tmp/celery_worker.log"
echo "   - Ver logs Beat:   tail -f /tmp/celery_beat.log"
echo "   - Iniciar Django:  python manage.py runserver 0.0.0.0:8000"
echo "   - Admin URL:       http://localhost:8000/admin/"
echo ""
echo "🛑 Para detener servicios: ./stop_services.sh"
echo ""
