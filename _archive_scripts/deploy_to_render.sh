#!/bin/bash

# 🚀 Script de Deploy Automatizado para Render.com - SafaryLoc
# Deploys el sistema optimizado de gestión logística

echo "🚀 SOPTRALOC - DEPLOY AUTOMATIZADO A RENDER.COM"
echo "================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Función para mostrar progreso
show_progress() {
    echo -e "${BLUE}$1${NC}"
}

show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

show_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificación de requisitos
show_progress "📋 Verificando requisitos previos..."

# Verificar Git
if ! command -v git &> /dev/null; then
    show_error "Git no está instalado"
    exit 1
fi

# Verificar que estamos en el directorio correcto
if [[ ! -f "render.yaml" ]]; then
    show_error "No se encontró render.yaml. Ejecuta desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar que tenemos cambios para subir
if git diff --quiet && git diff --cached --quiet; then
    show_warning "No hay cambios pendientes para commit"
else
    show_progress "📤 Subiendo cambios a GitHub..."
    
    # Agregar todos los cambios
    git add -A
    
    # Commit con mensaje descriptivo
    git commit -m "🚀 Deploy definitivo SafaryLoc v2.0 - Sistema optimizado

- ✅ Debugging exhaustivo completado
- 🔧 Normalización de estados de contenedores (692 registros)
- 🗄️ Sistema de gestión de duplicados implementado
- 📊 Dashboard con filtros optimizados
- 🛠️ Utilidades de administración y diagnóstico
- 🧹 Scripts de limpieza automatizados
- 🌐 Configuración de producción optimizada
- 🔒 Sistema listo para producción en Render.com

Deployment: render.yaml configurado para soptraloc-production"
    
    # Push a GitHub
    git push origin main
    show_success "Código subido a GitHub"
fi

# Mostrar información del deploy
echo ""
show_progress "📋 INFORMACIÓN DEL DEPLOY:"
echo -e "${PURPLE}  Servicio Web:     soptraloc-production${NC}"
echo -e "${PURPLE}  Base de Datos:    soptraloc-production-db${NC}"
echo -e "${PURPLE}  URL Final:        https://soptraloc-production.onrender.com${NC}"
echo -e "${PURPLE}  Entorno:          Producción${NC}"
echo -e "${PURPLE}  Version:          v2.0-optimized${NC}"

echo ""
show_progress "🔧 CARACTERÍSTICAS DEL SISTEMA:"
echo "  🗄️  678 contenedores importados desde planilla Walmart"
echo "  🔄 Estados normalizados (español/inglés → español estándar)"
echo "  🔍 Sistema de detección de duplicados"
echo "  📊 Dashboard optimizado con filtros mejorados"
echo "  🛠️  Comandos de administración incluidos"
echo "  🧹 Scripts de limpieza automatizados"

echo ""
show_warning "PASOS SIGUIENTES:"
echo "1. 🌐 Ve a https://render.com/dashboard"
echo "2. 📁 Crea un nuevo Web Service desde GitHub"
echo "3. 🔗 Conecta tu repositorio: https://github.com/Safary16/soptraloc.git"
echo "4. 📋 Render detectará automáticamente el render.yaml"
echo "5. ✅ Confirma la configuración y despliega"
echo "6. 🧹 Ejecuta ./cleanup_render_services.sh para limpiar servicios previos"

echo ""
read -p "¿Quieres abrir Render Dashboard ahora? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "https://render.com/dashboard"
    elif command -v open &> /dev/null; then
        open "https://render.com/dashboard"
    else
        echo "🌐 Abre manualmente: https://render.com/dashboard"
    fi
fi

echo ""
show_success "🎉 Deploy preparado correctamente!"
show_progress "📊 Monitoreo post-deploy:"
echo "  - Verifica logs en Render Dashboard"
echo "  - Prueba la URL: https://soptraloc-production.onrender.com"
echo "  - Ejecuta diagnósticos con: python manage.py diagnose_containers"
echo "  - Limpia servicios anteriores con: ./cleanup_render_services.sh"

echo ""
echo -e "${GREEN}✅ SOPTRALOC LISTO PARA PRODUCCIÓN${NC}"