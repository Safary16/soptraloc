#!/bin/bash
# Script para ejecutar en Render Shell después del deploy
# Sincroniza todo: migraciones, ubicaciones, limpieza de conductores

set -e  # Salir si hay error

echo "=================================================="
echo "  CONFIGURACIÓN POST-DEPLOY - SOPTRALOC TMS"
echo "=================================================="
echo ""

# 1. Verificar estado actual
echo "1️⃣  Verificando estado actual del sistema..."
python manage.py verify_production

echo ""
echo "=================================================="
echo "2️⃣  Aplicando migraciones..."
python manage.py migrate --noinput

echo ""
echo "=================================================="
echo "3️⃣  Cargando ubicaciones iniciales (si no existen)..."
python manage.py load_initial_times

echo ""
echo "=================================================="
echo "4️⃣  Revisando conductores antes de limpieza..."
python manage.py aggressive_cleanup --dry-run

echo ""
echo "=================================================="
read -p "¿Desea continuar con la limpieza de conductores? (escriba ELIMINAR): " confirm

if [ "$confirm" = "ELIMINAR" ]; then
    echo ""
    echo "5️⃣  Ejecutando limpieza de conductores..."
    python manage.py aggressive_cleanup --force --keep=50
    
    echo ""
    echo "=================================================="
    echo "6️⃣  Verificación final..."
    python manage.py verify_production
    
    echo ""
    echo "✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE"
else
    echo ""
    echo "⚠️  Limpieza de conductores cancelada"
    echo "Puede ejecutarla manualmente con:"
    echo "  python manage.py aggressive_cleanup --force --keep=50"
fi

echo ""
echo "=================================================="
echo "Sistema listo para usar en producción"
echo "Accede al dashboard para verificar Mapbox"
echo "=================================================="
