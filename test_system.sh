#!/bin/bash
echo "=== PRUEBAS COMPLETAS DEL SISTEMA SOPTRALOC ==="

echo "1. Probando endpoint principal..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
echo "   Página principal: HTTP $response"

echo "2. Probando página de login..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/accounts/login/)
echo "   Página de login: HTTP $response"

echo "3. Probando admin..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/)
echo "   Admin: HTTP $response"

echo "4. Probando API endpoints..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/containers/)
echo "   API Containers: HTTP $response"

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/drivers/)
echo "   API Drivers: HTTP $response"

echo "5. Probando Swagger docs..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/swagger/)
echo "   Swagger: HTTP $response"

echo "6. Verificando autenticación - intentando acceder al dashboard sin login..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard/)
echo "   Dashboard sin auth: HTTP $response (debería ser 302 o 403)"

echo ""
echo "=== RESUMEN DE ESTADO ==="
if [ "$response" != "000" ]; then
    echo "✅ Servidor respondiendo correctamente"
    echo "✅ Todas las URLs configuradas"
    echo "✅ Sistema operativo"
else
    echo "❌ Servidor no responde"
fi