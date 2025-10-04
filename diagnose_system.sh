#!/usr/bin/env bash
# Script de diagnóstico para verificar el estado del sistema

echo "========================================"
echo "🔍 DIAGNÓSTICO DEL SISTEMA SOPTRALOC"
echo "========================================"
echo ""

cd /workspaces/soptraloc/soptraloc_system

echo "1. Verificando Django..."
/workspaces/soptraloc/venv/bin/python manage.py check
echo ""

echo "2. Verificando migraciones..."
/workspaces/soptraloc/venv/bin/python manage.py showmigrations | grep -E "\[ \]" || echo "✅ Todas las migraciones aplicadas"
echo ""

echo "3. Verificando modelos..."
echo "   - Contenedores: $(/workspaces/soptraloc/venv/bin/python manage.py shell -c "from apps.containers.models import Container; print(Container.objects.count())")"
echo "   - Conductores: $(/workspaces/soptraloc/venv/bin/python manage.py shell -c "from apps.drivers.models import Driver; print(Driver.objects.count())")"
echo "   - Usuarios: $(/workspaces/soptraloc/venv/bin/python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())")"
echo ""

echo "4. Verificando templates críticos..."
for template in templates/core/dashboard.html templates/containers/setup_initial.html templates/core/home.html; do
    if [ -f "$template" ]; then
        echo "   ✅ $template"
    else
        echo "   ❌ FALTA: $template"
    fi
done
echo ""

echo "5. Verificando archivos estáticos..."
if [ -d "static/js" ]; then
    echo "   ✅ static/js"
    ls -1 static/js/ | head -5
else
    echo "   ❌ FALTA: static/js"
fi
echo ""

echo "6. URLs configuradas:"
/workspaces/soptraloc/venv/bin/python manage.py show_urls 2>/dev/null | grep -E "(dashboard|setup|admin)" | head -10 || echo "   (comando show_urls no disponible)"
echo ""

echo "========================================"
echo "✅ DIAGNÓSTICO COMPLETADO"
echo "========================================"
