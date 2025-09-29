#!/bin/bash

echo "🔑 GENERANDO TOKEN JWT PARA TESTING"
echo "================================="

cd /workspaces/soptraloc/soptraloc_system

# Crear token JWT
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

# Obtener el usuario admin
try:
    user = User.objects.get(username='admin')
    print(f"✅ Usuario encontrado: {user.username}")
    
    # Generar token JWT
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    print("\n🎟️  TOKEN DE ACCESO:")
    print("=" * 50)
    print(access_token)
    
    print("\n🔄 TOKEN DE REFRESH:")
    print("=" * 50)
    print(refresh_token)
    
    print("\n💡 COMO USAR:")
    print("=" * 50)
    print("En las peticiones HTTP, añade el header:")
    print(f"Authorization: Bearer {access_token}")
    
    print("\n🌐 EJEMPLO CURL:")
    print("=" * 50)
    print(f'curl -H "Authorization: Bearer {access_token}" http://localhost:8000/api/v1/containers/')
    
except User.DoesNotExist:
    print("❌ Usuario admin no encontrado")
    print("Creando usuario admin...")
    user = User.objects.create_superuser('admin', 'admin@soptraloc.local', 'admin123')
    refresh = RefreshToken.for_user(user)
    print(f"✅ Usuario creado y token generado: {str(refresh.access_token)}")

EOF

echo ""
echo "✅ Token generado exitosamente"