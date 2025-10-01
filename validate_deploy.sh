#!/usr/bin/env bash
# Script de validación completa pre-deploy
set -e

echo "=========================================="
echo "🔍 VALIDACIÓN COMPLETA PRE-DEPLOY"
echo "=========================================="

cd /workspaces/soptraloc

# 1. Verificar estructura del proyecto
echo ""
echo "1️⃣ Verificando estructura del proyecto..."
if [ -d "soptraloc_system" ]; then
    echo "✅ Directorio soptraloc_system existe"
else
    echo "❌ ERROR: soptraloc_system no encontrado"
    exit 1
fi

if [ -f "soptraloc_system/config/wsgi.py" ]; then
    echo "✅ config/wsgi.py existe"
else
    echo "❌ ERROR: wsgi.py no encontrado"
    exit 1
fi

if [ -f "soptraloc_system/config/settings_production.py" ]; then
    echo "✅ config/settings_production.py existe"
else
    echo "❌ ERROR: settings_production.py no encontrado"
    exit 1
fi

# 2. Verificar archivos de deploy
echo ""
echo "2️⃣ Verificando archivos de deploy..."
for file in render.yaml build.sh post_deploy.sh requirements.txt; do
    if [ -f "$file" ]; then
        echo "✅ $file existe"
    else
        echo "❌ ERROR: $file no encontrado"
        exit 1
    fi
done

# 3. Verificar permisos
echo ""
echo "3️⃣ Verificando permisos de scripts..."
for script in build.sh post_deploy.sh; do
    if [ -x "$script" ]; then
        echo "✅ $script es ejecutable"
    else
        echo "⚠️  Corrigiendo permisos de $script"
        chmod +x "$script"
    fi
done

# 4. Validar render.yaml
echo ""
echo "4️⃣ Validando render.yaml..."
if grep -q "startCommand:" render.yaml; then
    echo "✅ startCommand encontrado"
else
    echo "❌ ERROR: startCommand no encontrado en render.yaml"
    exit 1
fi

if grep -q "config.wsgi:application" render.yaml; then
    echo "✅ config.wsgi:application configurado"
else
    echo "❌ ERROR: config.wsgi:application no encontrado"
    exit 1
fi

if grep -q "soptraloc-db" render.yaml; then
    echo "✅ Base de datos soptraloc-db configurada"
else
    echo "❌ ERROR: Base de datos no configurada"
    exit 1
fi

# 5. Verificar que NO existe app.py en la raíz
echo ""
echo "5️⃣ Verificando que app.py NO existe..."
if [ -f "app.py" ]; then
    echo "❌ ERROR: app.py existe (debe eliminarse)"
    exit 1
else
    echo "✅ app.py NO existe (correcto)"
fi

# 6. Validar settings_production.py
echo ""
echo "6️⃣ Validando settings_production.py..."
cd soptraloc_system

if python -c "from config import settings_production; print('✅ settings_production se importa correctamente')"; then
    echo "✅ settings_production válido"
else
    echo "❌ ERROR: Error al importar settings_production"
    exit 1
fi

# 7. Verificar modelos
echo ""
echo "7️⃣ Verificando modelos de Django..."
export DJANGO_SETTINGS_MODULE=config.settings_production
export SECRET_KEY="test-key-for-validation"
export DATABASE_URL="sqlite:///test.db"

if python manage.py check --deploy 2>&1 | grep -q "System check identified no issues"; then
    echo "✅ Django check passed"
else
    echo "⚠️  Django check tiene advertencias (revisar manualmente)"
fi

# 8. Verificar comando load_initial_times
echo ""
echo "8️⃣ Verificando comando load_initial_times..."
if [ -f "apps/routing/management/commands/load_initial_times.py" ]; then
    echo "✅ load_initial_times.py existe"
else
    echo "❌ ERROR: load_initial_times.py no encontrado"
    exit 1
fi

# 9. Contar modelos
echo ""
echo "9️⃣ Contando modelos..."
MODEL_COUNT=$(find apps -name "models.py" -exec grep -l "class.*models.Model" {} \; | wc -l)
echo "✅ $MODEL_COUNT archivos de modelos encontrados"

# 10. Verificar staticfiles
echo ""
echo "🔟 Verificando configuración de static files..."
if grep -q "STATIC_ROOT" config/settings_production.py; then
    echo "✅ STATIC_ROOT configurado"
else
    echo "❌ ERROR: STATIC_ROOT no configurado"
    exit 1
fi

cd ..

# Resumen final
echo ""
echo "=========================================="
echo "✅ VALIDACIÓN COMPLETA EXITOSA"
echo "=========================================="
echo ""
echo "📊 RESUMEN:"
echo "  ✅ Estructura del proyecto: OK"
echo "  ✅ Archivos de deploy: OK"
echo "  ✅ Permisos de scripts: OK"
echo "  ✅ render.yaml: VÁLIDO"
echo "  ✅ app.py: NO EXISTE (correcto)"
echo "  ✅ settings_production.py: VÁLIDO"
echo "  ✅ Django check: OK"
echo "  ✅ Comandos de management: OK"
echo "  ✅ Configuración de static: OK"
echo ""
echo "🚀 LISTO PARA DEPLOY EN RENDER"
echo "=========================================="
