#!/bin/bash
# Script de Debugging Profesional Completo
# Sistema SoptraLoc - Verificación Pre-Deploy

echo "=========================================="
echo "🔍 DEBUGGING PROFESIONAL COMPLETO"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de errores
ERRORS=0
WARNINGS=0

# Función para reportar errores
report_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((ERRORS++))
}

report_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

report_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Cambiar al directorio del proyecto
cd /workspaces/soptraloc/soptraloc_system || exit 1

echo "1️⃣  VERIFICANDO SINTAXIS PYTHON"
echo "----------------------------------------"

# Verificar sintaxis de archivos críticos
CRITICAL_FILES=(
    "config/settings.py"
    "config/settings_production.py"
    "config/urls.py"
    "config/wsgi.py"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        if python -m py_compile "$file" 2>/dev/null; then
            report_success "Sintaxis OK: $file"
        else
            report_error "Sintaxis inválida: $file"
        fi
    else
        report_warning "Archivo no encontrado: $file"
    fi
done

echo ""
echo "2️⃣  VERIFICANDO MODELOS DE APPS"
echo "----------------------------------------"

python manage.py shell -c "
from django.apps import apps

custom_apps = ['core', 'containers', 'drivers', 'routing', 'warehouses', 'alerts', 'optimization', 'scheduling']

for app_name in custom_apps:
    try:
        app = apps.get_app_config(app_name)
        models = list(app.get_models())
        if len(models) == 0:
            print(f'⚠️  {app_name}: APP VACÍA ({len(models)} modelos)')
        else:
            print(f'✅ {app_name}: {len(models)} modelos')
    except Exception as e:
        print(f'❌ {app_name}: ERROR - {e}')
" 2>&1

echo ""
echo "3️⃣  DJANGO SYSTEM CHECK"
echo "----------------------------------------"

if python manage.py check 2>&1 | grep -q "System check identified no issues"; then
    report_success "System check passed"
else
    report_warning "System check tiene issues"
    python manage.py check 2>&1 | grep -E "ERROR|WARNING" | head -5
fi

echo ""
echo "4️⃣  VERIFICANDO MIGRACIONES"
echo "----------------------------------------"

PENDING=$(python manage.py showmigrations 2>&1 | grep "\[ \]" | wc -l)
if [ "$PENDING" -eq 0 ]; then
    report_success "Todas las migraciones aplicadas"
else
    report_error "$PENDING migraciones pendientes"
    python manage.py showmigrations 2>&1 | grep "\[ \]" | head -5
fi

echo ""
echo "5️⃣  VERIFICANDO DEPENDENCIAS"
echo "----------------------------------------"

if pip check 2>&1 | grep -q "No broken requirements found"; then
    report_success "Todas las dependencias OK"
else
    report_warning "Problemas con dependencias"
    pip check 2>&1 | head -5
fi

echo ""
echo "6️⃣  VERIFICANDO ARCHIVOS ESTÁTICOS"
echo "----------------------------------------"

if [ -d "staticfiles" ]; then
    STATIC_COUNT=$(find staticfiles -type f | wc -l)
    report_success "Staticfiles: $STATIC_COUNT archivos"
else
    report_warning "Directorio staticfiles no existe"
fi

echo ""
echo "7️⃣  VERIFICANDO CONFIGURACIÓN DE PRODUCCIÓN"
echo "----------------------------------------"

# Verificar variables críticas en settings_production.py
if grep -q "DEBUG = False" config/settings_production.py; then
    report_success "DEBUG = False en producción"
else
    report_error "DEBUG no está en False"
fi

if grep -q "ALLOWED_HOSTS" config/settings_production.py; then
    report_success "ALLOWED_HOSTS configurado"
else
    report_error "ALLOWED_HOSTS no configurado"
fi

if grep -q "SECRET_KEY" config/settings_production.py; then
    report_success "SECRET_KEY presente"
else
    report_error "SECRET_KEY no encontrada"
fi

echo ""
echo "8️⃣  VERIFICANDO URLS"
echo "----------------------------------------"

python manage.py shell -c "
from django.urls import get_resolver
from django.urls.exceptions import NoReverseMatch

resolver = get_resolver()
patterns = resolver.url_patterns
print(f'✅ URLs configuradas: {len(patterns)} patrones')

# Verificar URLs críticas
critical_urls = ['dashboard/', 'admin/', 'api/v1/containers/', 'api/v1/routing/']
for url in critical_urls:
    try:
        from django.urls import resolve
        match = resolve('/' + url)
        print(f'✅ {url} -> {match.view_name}')
    except:
        print(f'⚠️  {url} -> No encontrada')
" 2>&1

echo ""
echo "9️⃣  VERIFICANDO APPS VACÍAS"
echo "----------------------------------------"

if [ -d "apps/alerts" ] && [ -f "apps/alerts/models.py" ]; then
    if grep -q "^class.*Model" apps/alerts/models.py; then
        report_success "apps.alerts tiene modelos"
    else
        report_warning "apps.alerts está vacía (puede eliminarse)"
    fi
fi

if [ -d "apps/optimization" ] && [ -f "apps/optimization/models.py" ]; then
    if grep -q "^class.*Model" apps/optimization/models.py; then
        report_success "apps.optimization tiene modelos"
    else
        report_warning "apps.optimization está vacía (puede eliminarse)"
    fi
fi

if [ -d "apps/scheduling" ] && [ -f "apps/scheduling/models.py" ]; then
    if grep -q "^class.*Model" apps/scheduling/models.py; then
        report_success "apps.scheduling tiene modelos"
    else
        report_warning "apps.scheduling está vacía (puede eliminarse)"
    fi
fi

echo ""
echo "🔟  VERIFICANDO INTEGRACIÓN ML"
echo "----------------------------------------"

python manage.py shell -c "
try:
    from apps.routing.ml_service import TimePredictionML
    ml = TimePredictionML()
    print('✅ ML Service importado correctamente')
    
    from apps.routing.models import LocationPair, OperationTime
    lp_count = LocationPair.objects.count()
    op_count = OperationTime.objects.count()
    print(f'✅ LocationPairs: {lp_count}')
    print(f'✅ OperationTimes: {op_count}')
except Exception as e:
    print(f'❌ Error en ML: {e}')
" 2>&1

echo ""
echo "1️⃣1️⃣  VERIFICANDO TEMPLATES"
echo "----------------------------------------"

if [ -f "templates/base.html" ]; then
    if grep -q "atc-clock" templates/base.html; then
        report_success "Reloj ATC presente en base.html"
    else
        report_warning "Reloj ATC no encontrado en base.html"
    fi
else
    report_error "templates/base.html no encontrado"
fi

echo ""
echo "1️⃣2️⃣  VERIFICANDO JAVASCRIPT"
echo "----------------------------------------"

if [ -f "static/js/realtime-clock.js" ]; then
    if grep -q "class ATCClock" static/js/realtime-clock.js; then
        report_success "Clase ATCClock presente"
    else
        report_warning "Clase ATCClock no encontrada"
    fi
else
    report_error "realtime-clock.js no encontrado"
fi

echo ""
echo "1️⃣3️⃣  VERIFICANDO ARCHIVOS DE DEPLOY"
echo "----------------------------------------"

DEPLOY_FILES=(
    "render.yaml"
    "build.sh"
    "requirements.txt"
)

for file in "${DEPLOY_FILES[@]}"; do
    if [ -f "../$file" ] || [ -f "$file" ]; then
        report_success "Archivo presente: $file"
    else
        report_error "Archivo faltante: $file"
    fi
done

echo ""
echo "1️⃣4️⃣  SIMULANDO DEPLOY CHECK"
echo "----------------------------------------"

python manage.py check --deploy 2>&1 | grep -E "ERROR|WARNING" | while read line; do
    if echo "$line" | grep -q "ERROR"; then
        report_error "$line"
    else
        report_warning "$line"
    fi
done

echo ""
echo "=========================================="
echo "📊 RESUMEN FINAL"
echo "=========================================="
echo -e "${RED}Errores críticos: $ERRORS${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ SISTEMA LISTO PARA DEPLOY${NC}"
    exit 0
else
    echo -e "${RED}❌ CORREGIR ERRORES ANTES DE DEPLOY${NC}"
    exit 1
fi
