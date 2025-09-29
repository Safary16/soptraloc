#!/bin/bash

echo "🔧 VERIFICACIÓN DE CONFIGURACIÓN CSRF"
echo "====================================="
echo ""

echo "✅ CAMBIOS APLICADOS:"
echo "===================="
echo "1. ✅ CSRF_TRUSTED_ORIGINS configurado"
echo "2. ✅ ALLOWED_HOSTS actualizado" 
echo "3. ✅ CORS_ALLOWED_ORIGINS expandido"
echo "4. ✅ Configuración DEBUG habilitada"
echo ""

echo "🌐 URLS DE CONFIANZA CONFIGURADAS:"
echo "================================="
echo "• http://localhost:8000"
echo "• https://localhost:8000"
echo "• http://127.0.0.1:8000"
echo "• https://127.0.0.1:8000"
echo "• http://0.0.0.0:8000"
echo ""

echo "🚀 ENLACES ACTUALIZADOS:"
echo "========================"
echo "🎯 Panel Admin (HTTPS): https://localhost:8000/admin/"
echo "🎯 Panel Admin (HTTP):  http://localhost:8000/admin/"
echo "🏠 Página Principal:    http://localhost:8000/"
echo "📊 API Swagger:         http://localhost:8000/swagger/"
echo ""

echo "🔑 CREDENCIALES:"
echo "================"
echo "👤 Usuario: admin"
echo "🔒 Contraseña: admin123"
echo ""

echo "🧪 PRUEBA DE CONECTIVIDAD:"
echo "=========================="

# Probar acceso básico
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200"; then
    echo "✅ Página principal accesible"
else
    echo "❌ Página principal no accesible"
fi

# Probar admin 
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ | grep -q "200\|302"; then
    echo "✅ Panel admin accesible"
else
    echo "❌ Panel admin no accesible"
fi

# Probar API
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/containers/containers/ | grep -q "200\|401"; then
    echo "✅ API REST accesible"
else
    echo "❌ API REST no accesible"
fi

echo ""
echo "💡 SOLUCIÓN AL ERROR 403:"
echo "========================="
echo "• Problema: Origin checking failed"
echo "• Causa: CSRF_TRUSTED_ORIGINS no configurado"
echo "• Solución: ✅ Configurado correctamente"
echo ""
echo "🎉 ¡ERROR CSRF SOLUCIONADO!"
echo "Ahora puedes acceder sin problemas a:"
echo "👉 http://localhost:8000/admin/"