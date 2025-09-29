#!/bin/bash

echo "🧪 PRUEBA RÁPIDA DE APIS"
echo "======================="

# Esperar a que el servidor esté listo
sleep 2

echo "1. 📋 Información de autenticación:"
echo "GET /api/v1/auth/info/"
curl -s http://localhost:8000/api/v1/auth/info/ | python -m json.tool
echo ""

echo "2. 📦 Containers API (sin autenticación en modo DEBUG):"
echo "GET /api/v1/containers/"
curl -s http://localhost:8000/api/v1/containers/ | python -m json.tool
echo ""

echo "3. 🏠 Página principal:"
echo "GET /"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8000/
echo ""

echo "4. 🏥 Health Check:"
echo "GET /health/"
curl -s http://localhost:8000/health/ | python -m json.tool
echo ""

echo "✅ Pruebas completadas"