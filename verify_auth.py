#!/usr/bin/env python
"""
Script de verificación de autenticación para producción
Verifica y crea el superusuario si es necesario
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'soptraloc_system'))
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def verify_database():
    """Verificar conexión a la base de datos"""
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DE BASE DE DATOS")
    print("="*60)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"✅ Conexión PostgreSQL exitosa")
            print(f"   Versión: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def verify_users():
    """Verificar usuarios existentes"""
    print("\n" + "="*60)
    print("👥 VERIFICACIÓN DE USUARIOS")
    print("="*60)
    
    try:
        total_users = User.objects.count()
        print(f"Total de usuarios: {total_users}")
        
        if total_users > 0:
            print("\nUsuarios existentes:")
            for user in User.objects.all():
                print(f"  - {user.username}")
                print(f"    Email: {user.email}")
                print(f"    Superusuario: {user.is_superuser}")
                print(f"    Staff: {user.is_staff}")
                print(f"    Activo: {user.is_active}")
                print()
        
        return True
    except Exception as e:
        print(f"❌ Error verificando usuarios: {e}")
        return False

def create_superuser():
    """Crear superusuario si no existe"""
    print("\n" + "="*60)
    print("👤 CREACIÓN DE SUPERUSUARIO")
    print("="*60)
    
    username = 'admin'
    email = 'admin@soptraloc.com'
    password = '1234'
    
    try:
        # Verificar si existe
        if User.objects.filter(username=username).exists():
            print(f"ℹ️  Usuario '{username}' ya existe")
            
            # Verificar contraseña
            user = User.objects.get(username=username)
            if user.check_password(password):
                print(f"✅ Contraseña verificada correctamente")
            else:
                print(f"⚠️  ADVERTENCIA: La contraseña NO coincide con '1234'")
                print(f"   Reseteando contraseña...")
                user.set_password(password)
                user.save()
                print(f"✅ Contraseña reseteada a: 1234")
            
            # Asegurar permisos
            if not user.is_superuser or not user.is_staff:
                print(f"⚠️  Ajustando permisos de superusuario...")
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.save()
                print(f"✅ Permisos actualizados")
            
            return True
        
        # Crear nuevo superusuario
        print(f"Creando superusuario '{username}'...")
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Superusuario creado exitosamente")
        print(f"\n🔐 CREDENCIALES:")
        print(f"   Usuario: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print(f"\n⚠️  IMPORTANTE: Cambiar esta contraseña en /admin/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando superusuario: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication():
    """Probar autenticación"""
    print("\n" + "="*60)
    print("🔐 PRUEBA DE AUTENTICACIÓN")
    print("="*60)
    
    from django.contrib.auth import authenticate
    
    username = 'admin'
    password = '1234'
    
    try:
        user = authenticate(username=username, password=password)
        
        if user is not None:
            print(f"✅ Autenticación exitosa para '{username}'")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Superusuario: {user.is_superuser}")
            print(f"   Staff: {user.is_staff}")
            print(f"   Activo: {user.is_active}")
            return True
        else:
            print(f"❌ Autenticación FALLIDA para '{username}'")
            print(f"   Las credenciales no son válidas")
            return False
            
    except Exception as e:
        print(f"❌ Error durante autenticación: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🚀 VERIFICACIÓN DE AUTENTICACIÓN - SOPTRALOC TMS")
    print("="*60)
    print(f"Entorno: {os.environ.get('DJANGO_SETTINGS_MODULE', 'No configurado')}")
    print(f"Python: {sys.version.split()[0]}")
    print("="*60)
    
    # Ejecutar verificaciones
    results = []
    
    results.append(("Base de datos", verify_database()))
    results.append(("Usuarios", verify_users()))
    results.append(("Superusuario", create_superuser()))
    results.append(("Autenticación", test_authentication()))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    for name, success in results:
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {'OK' if success else 'FALLÓ'}")
    
    all_success = all(success for _, success in results)
    
    print("="*60)
    if all_success:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("\n🔗 Puedes acceder al admin en:")
        print("   https://soptraloc.onrender.com/admin/")
        print("\n🔐 Credenciales:")
        print("   Usuario: admin")
        print("   Password: 1234")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("   Revisa los errores arriba")
    
    print("="*60 + "\n")
    
    return 0 if all_success else 1

if __name__ == '__main__':
    sys.exit(main())
