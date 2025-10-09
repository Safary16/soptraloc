#!/bin/bash
#
# Script para detener todos los servicios de SOPTRALOC TMS
# Uso: ./stop_services.sh
#

echo "======================================================================="
echo "  🛑 DETENIENDO SOPTRALOC TMS"
echo "======================================================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Detener Celery Worker
echo "1️⃣  Deteniendo Celery Worker..."
if pkill -f "celery.*worker"; then
    echo -e "${GREEN}✅ Celery Worker detenido${NC}"
else
    echo -e "${YELLOW}⚠️  Celery Worker no estaba corriendo${NC}"
fi

# 2. Detener Celery Beat
echo "2️⃣  Deteniendo Celery Beat..."
if pkill -f "celery.*beat"; then
    echo -e "${GREEN}✅ Celery Beat detenido${NC}"
else
    echo -e "${YELLOW}⚠️  Celery Beat no estaba corriendo${NC}"
fi

# 3. Detener Django (si está corriendo)
echo "3️⃣  Deteniendo Django Server..."
if pkill -f "manage.py runserver"; then
    echo -e "${GREEN}✅ Django Server detenido${NC}"
else
    echo -e "${YELLOW}⚠️  Django Server no estaba corriendo${NC}"
fi

# 4. Opcionalmente detener Redis
echo ""
echo "❓ ¿Detener Redis también? (y/n)"
read -t 5 -r REPLY || REPLY="n"
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "4️⃣  Deteniendo Redis..."
    redis-cli shutdown
    echo -e "${GREEN}✅ Redis detenido${NC}"
else
    echo "   Redis sigue corriendo (puede ser usado por otros servicios)"
fi

echo ""
echo "======================================================================="
echo -e "  ${GREEN}✅ SERVICIOS DETENIDOS${NC}"
echo "======================================================================="
echo ""
