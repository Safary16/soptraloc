#!/bin/bash

echo "🔑 CONFIGURACIÓN DE USUARIO ADMIN"
echo "================================="
echo ""

cd /workspaces/soptraloc/soptraloc_system

# Verificar y crear/actualizar usuario admin
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
import os

print("🔍 Verificando usuario admin...")

try:
    # Buscar usuario admin existente
    user = User.objects.get(username='admin')
    print(f"✅ Usuario admin encontrado: {user.username}")
    print(f"📧 Email: {user.email}")
    print(f"👑 Es superuser: {user.is_superuser}")
    print(f"🔧 Es staff: {user.is_staff}")
    
    # Actualizar contraseña
    user.set_password('admin123')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print("🔒 Contraseña actualizada: admin123")
    
except User.DoesNotExist:
    print("❌ Usuario admin no encontrado. Creando nuevo usuario...")
    
    # Crear nuevo superusuario
    user = User.objects.create_superuser(
        username='admin',
        email='admin@soptraloc.local',
        password='admin123'
    )
    print("✅ Usuario admin creado exitosamente")
    print(f"👤 Username: {user.username}")
    print(f"📧 Email: {user.email}")

print("")
print("🎯 CREDENCIALES FINALES:")
print("========================")
print("👤 Usuario: admin")
print("🔒 Contraseña: admin123")
print("📧 Email: admin@soptraloc.local")
print("")
print("🌐 URLs de acceso:")
print("• Panel Admin: http://localhost:8000/admin/")
print("• Página Principal: http://localhost:8000/")

# Verificar que el usuario puede autenticarse
from django.contrib.auth import authenticate
auth_user = authenticate(username='admin', password='admin123')
if auth_user:
    print("✅ Autenticación verificada: FUNCIONA")
else:
    print("❌ Error en autenticación")

EOF

echo ""
echo "🚀 USUARIO CONFIGURADO CORRECTAMENTE"
echo "Ahora puedes acceder a http://localhost:8000/admin/"