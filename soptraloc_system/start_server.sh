#!/bin/bash

# Script para iniciar y verificar el servidor SOPTRALOC
echo "🚀 INICIANDO SERVIDOR SOPTRALOC"
echo "================================"

# Ir al directorio correcto
cd /workspaces/soptraloc/soptraloc_system

# Activar entorno virtual
echo "🐍 Activando entorno virtual..."
source ../venv/bin/activate

# Verificar sistema
echo "⚙️ Verificando sistema Django..."
python manage.py check

# Mostrar estadísticas
echo "📊 Estadísticas del sistema:"
python manage.py shell -c "
from apps.containers.models import Container
from apps.drivers.models import Driver
print(f'Contenedores: {Container.objects.count()}')
print(f'Conductores: {Driver.objects.count()}')
print(f'Programados: {Container.objects.filter(status=\"PROGRAMADO\").count()}')
"

echo ""
echo "🌐 Iniciando servidor en puerto 8000..."
echo "📋 Acceso:"
echo "   🏠 Principal: http://localhost:8000/"
echo "   🎯 Admin: http://localhost:8000/admin/ (admin/admin123)"
echo "   📊 Swagger: http://localhost:8000/swagger/"
echo "   📡 API: http://localhost:8000/api/v1/"
echo ""
echo "⚠️  Para detener: Ctrl+C"
echo "================================"
echo ""

# Iniciar servidor
python manage.py runserver 0.0.0.0:8000