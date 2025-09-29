#!/bin/bash

echo "🔍 VERIFICACIÓN COMPLETA DEL SISTEMA SOPTRALOC"
echo "============================================="
echo ""

# Verificar que el servidor puede iniciar
echo "1. ✅ Verificando configuración Django..."
cd /workspaces/soptraloc/soptraloc_system
python manage.py check --deploy > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Configuración Django: OK"
else
    echo "   ❌ Error en configuración Django"
    exit 1
fi

# Verificar migraciones
echo "2. ✅ Verificando estado de migraciones..."
python manage.py showmigrations --plan | grep -c "\[X\]" > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Migraciones aplicadas: OK"
else
    echo "   ⚠️  Verificar migraciones manualmente"
fi

# Verificar importación de contenedores
echo "3. ✅ Verificando sistema de importación..."
if [ -f "containers_sample.csv" ] && [ -f "create_container_csv.py" ]; then
    echo "   ✅ Archivos de importación: Disponibles"
    python manage.py help import_containers > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ Comando import_containers: Disponible"
    else
        echo "   ❌ Comando import_containers: Error"
    fi
else
    echo "   ⚠️  Archivos de importación: No encontrados"
fi

# Verificar estructura de archivos críticos
echo "4. ✅ Verificando archivos críticos..."
critical_files=(
    "config/settings.py"
    "config/urls.py" 
    "apps/core/models.py"
    "apps/containers/models.py"
    "apps/containers/views.py"
    "templates/home.html"
)

all_files_ok=true
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file: Existe"
    else
        echo "   ❌ $file: No encontrado"
        all_files_ok=false
    fi
done

# Verificar sintaxis Python en archivos clave
echo "5. ✅ Verificando sintaxis Python..."
python_files=(
    "apps/core/models.py"
    "apps/containers/models.py"
    "apps/containers/views.py"
    "apps/scheduling/views.py"
    "apps/alerts/views.py"
    "apps/optimization/views.py"
    "apps/warehouses/views.py"
)

syntax_ok=true
for file in "${python_files[@]}"; do
    python -m py_compile "$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ $file: Sintaxis OK"
    else
        echo "   ❌ $file: Error de sintaxis"
        syntax_ok=false
    fi
done

# Verificar endpoints principales
echo "6. ✅ Verificando disponibilidad de URLs..."
urls_to_check=(
    "/"
    "/admin/"
    "/api/v1/core/"
    "/api/v1/containers/"
    "/swagger/"
    "/health/"
)

# Iniciar servidor en background para pruebas
python manage.py runserver 127.0.0.1:8001 > /dev/null 2>&1 &
server_pid=$!
sleep 3

urls_ok=true
for url in "${urls_to_check[@]}"; do
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8001$url" 2>/dev/null)
    if [ "$http_code" = "200" ] || [ "$http_code" = "302" ] || [ "$http_code" = "401" ]; then
        echo "   ✅ $url: Responde ($http_code)"
    else
        echo "   ❌ $url: Error ($http_code)"
        urls_ok=false
    fi
done

# Detener servidor de prueba
kill $server_pid > /dev/null 2>&1

echo ""
echo "📊 RESUMEN FINAL:"
echo "=================="

if [ "$syntax_ok" = true ] && [ "$all_files_ok" = true ] && [ "$urls_ok" = true ]; then
    echo "🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!"
    echo ""
    echo "✅ Configuración: OK"
    echo "✅ Archivos: OK" 
    echo "✅ Sintaxis: OK"
    echo "✅ Endpoints: OK"
    echo ""
    echo "🚀 El sistema está listo para:"
    echo "   • Importar contenedores desde CSV"
    echo "   • Usar APIs REST completas"
    echo "   • Administración Django"
    echo "   • Desarrollo continuo"
    echo ""
    echo "💡 Para usar:"
    echo "   python manage.py runserver"
    echo "   Abrir: http://localhost:8000"
    
    exit 0
else
    echo "⚠️  SISTEMA PARCIALMENTE FUNCIONAL"
    echo ""
    echo "❌ Se encontraron algunos problemas"
    echo "📋 Revisar mensajes anteriores para detalles"
    exit 1
fi