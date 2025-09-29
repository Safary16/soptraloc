#!/bin/bash

echo "🔐 INFORMACIÓN DE ACCESO AL SERVIDOR SOPTRALOC"
echo "=============================================="
echo ""

# Verificar si el servidor está ejecutándose
if pgrep -f "python manage.py runserver" > /dev/null; then
    SERVER_STATUS="✅ EJECUTÁNDOSE"
else
    SERVER_STATUS="❌ DETENIDO"
fi

echo "📊 ESTADO DEL SERVIDOR:"
echo "======================"
echo "Estado: $SERVER_STATUS"
echo ""

echo "🌐 ENLACES DE ACCESO:"
echo "===================="
echo "🏠 Página Principal:     http://localhost:8000/"
echo "⚙️  Panel de Administración: http://localhost:8000/admin/"
echo "🔗 APIs REST:            http://localhost:8000/api/v1/"
echo "📚 Documentación API:    http://localhost:8000/swagger/"
echo "🏥 Health Check:         http://localhost:8000/health/"
echo ""

echo "🔑 CREDENCIALES DE ADMINISTRADOR:"
echo "================================="
echo "👤 Usuario: admin"
echo "🔒 Contraseña: admin123"
echo "📧 Email: admin@soptraloc.local"
echo ""

echo "🎟️  ACCESO A APIS (JWT):"
echo "========================"
echo "Endpoint Token: http://localhost:8000/api/v1/auth/token/"
echo "Información Auth: http://localhost:8000/api/v1/auth/info/"
echo ""
echo "📝 Para obtener token JWT:"
echo 'curl -X POST http://localhost:8000/api/v1/auth/token/ \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{"username": "admin", "password": "admin123"}'\'''
echo ""

echo "🗂️  ESTRUCTURA DE APIS:"
echo "======================"
echo "📦 Contenedores:    /api/v1/containers/"
echo "🏭 Almacenes:       /api/v1/warehouses/" 
echo "📅 Programación:    /api/v1/scheduling/"
echo "🚨 Alertas:         /api/v1/alerts/"
echo "⚡ Optimización:    /api/v1/optimization/"
echo "🔧 Core:            /api/v1/core/"
echo ""

echo "💻 ACCESO DIRECTO AL SISTEMA:"
echo "============================="
echo "🖥️  Terminal: Ya tienes acceso completo via VS Code"
echo "📁 Proyecto: /workspaces/soptraloc/soptraloc_system"
echo "👤 Usuario Sistema: $(whoami)"
echo "🖧 IP Local: $(hostname -I | awk '{print $1}')"
echo ""

echo "🔧 COMANDOS ÚTILES:"
echo "=================="
echo "• Iniciar servidor:    python manage.py runserver 0.0.0.0:8000"
echo "• Parar servidor:      pkill -f 'python manage.py runserver'"
echo "• Shell Django:        python manage.py shell"
echo "• Ver logs:            tail -f server.log"
echo "• Crear superuser:     python manage.py createsuperuser"
echo ""

echo "🎯 PRUEBA RÁPIDA:"
echo "================"
echo "1. Ve a: http://localhost:8000/admin/"
echo "2. Usa: admin / admin123"
echo "3. O ve a: http://localhost:8000/ (página principal)"
echo ""

# Probar conectividad
echo "🧪 PRUEBA DE CONECTIVIDAD:"
echo "=========================="
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200"; then
    echo "✅ Servidor accesible en http://localhost:8000/"
else
    echo "❌ Servidor no accesible - verificar estado"
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ | grep -q "200\|302"; then
    echo "✅ Panel admin accesible en http://localhost:8000/admin/"
else
    echo "❌ Panel admin no accesible"
fi

echo ""
echo "🚀 ¡LISTO PARA USAR!"