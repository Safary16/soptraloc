#!/bin/bash
# Script para limpiar servicios y blueprints innecesarios de Render
# Este script elimina todos los servicios previos para mantener solo el deploy final

echo "🧹 LIMPIEZA DE SERVICIOS RENDER - SOPTRALOC"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que render CLI esté instalado
if ! command -v render &> /dev/null; then
    echo -e "${RED}❌ Render CLI no está instalado${NC}"
    echo "Instálalo con: curl -fsSL https://render.com/install.sh | bash"
    exit 1
fi

echo -e "${BLUE}📋 Listando servicios actuales...${NC}"
render services list

echo ""
echo -e "${YELLOW}⚠️  ATENCIÓN: Este script eliminará TODOS los servicios de Render excepto el nuevo deploy${NC}"
echo -e "${YELLOW}   Solo debe ejecutarse después de confirmar que el nuevo servicio funciona correctamente${NC}"
echo ""
read -p "¿Continuar? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✅ Operación cancelada${NC}"
    exit 0
fi

# Lista de patrones de servicios a eliminar (ajusta según tus servicios)
SERVICES_TO_DELETE=(
    "soptraloc-test"
    "soptraloc-beta" 
    "soptraloc-staging"
    "safaryloc-test"
    "safaryloc-demo"
    "soptraloc-old"
    "soptraloc-backup"
    "soptraloc-dev"
)

echo -e "${BLUE}🗑️  Eliminando servicios innecesarios...${NC}"

for service in "${SERVICES_TO_DELETE[@]}"; do
    echo -e "${YELLOW}Buscando servicio: $service${NC}"
    
    # Intentar eliminar el servicio (render CLI devuelve error si no existe)
    if render services delete "$service" --yes 2>/dev/null; then
        echo -e "${GREEN}✅ Eliminado: $service${NC}"
    else
        echo -e "${RED}⚠️  No encontrado o ya eliminado: $service${NC}"
    fi
done

echo ""
echo -e "${BLUE}📋 Servicios restantes:${NC}"
render services list

echo ""
echo -e "${GREEN}🎉 Limpieza completada${NC}"
echo -e "${BLUE}💡 Recuerda:${NC}"
echo "   1. Verificar que el servicio principal (soptraloc-web) esté funcionando"
echo "   2. Configurar las variables de entorno en Render Dashboard"
echo "   3. Monitorear logs por posibles errores"

# Mostrar información del servicio principal
echo ""
echo -e "${BLUE}📊 Estado del servicio principal:${NC}"
render services show soptraloc-web 2>/dev/null || echo -e "${YELLOW}⚠️  Servicio 'soptraloc-web' no encontrado. Verifica el nombre correcto.${NC}"

echo ""
echo -e "${GREEN}✅ Script de limpieza finalizado${NC}"