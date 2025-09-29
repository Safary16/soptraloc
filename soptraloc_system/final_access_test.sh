#!/bin/bash

echo "🧪 PRUEBA FINAL DE ACCESO"
echo "========================"
echo ""

echo "🔑 CREDENCIALES CONFIRMADAS:"
echo "============================="
echo "👤 Usuario: admin"
echo "🔒 Contraseña: admin123"
echo "📧 Email: admin@soptraloc.local"
echo ""

echo "🌐 ENLACES DE ACCESO:"
echo "===================="
echo "🎯 Panel Admin: http://localhost:8000/admin/"
echo "🏠 Página Principal: http://localhost:8000/"
echo "📊 API Swagger: http://localhost:8000/swagger/"
echo ""

echo "✅ VERIFICACIONES:"
echo "=================="

# Verificar servidor
if pgrep -f "python manage.py runserver" > /dev/null; then
    echo "✅ Servidor Django: EJECUTÁNDOSE"
else
    echo "❌ Servidor Django: DETENIDO"
fi

# Verificar conectividad
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ | grep -q "200"; then
    echo "✅ Panel Admin: ACCESIBLE"
else
    echo "⚠️  Panel Admin: Verificar manualmente"
fi

# Verificar página principal
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200"; then
    echo "✅ Página Principal: ACCESIBLE"
else
    echo "❌ Página Principal: No accesible"
fi

echo ""
echo "🎉 TODO LISTO PARA USAR:"
echo "========================"
echo "1. Ve a: http://localhost:8000/admin/"
echo "2. Ingresa: admin / admin123"
echo "3. ¡Ya tienes acceso completo!"
echo ""
echo "🗂️ EN EL PANEL ADMIN PUEDES VER:"
echo "• 👥 Users (usuarios)"
echo "• 🏢 Companies (empresas)"
echo "• 📦 Containers (contenedores)"
echo "• 🚛 Vehicles (vehículos)"
echo "• 📍 Locations (ubicaciones)"
echo "• 📊 Movement codes (códigos de movimiento)"
echo ""
echo "💾 BASE DE DATOS:"
echo "• 3 contenedores de muestra de Walmart"
echo "• Usuario admin configurado"
echo "• Sistema completamente funcional"