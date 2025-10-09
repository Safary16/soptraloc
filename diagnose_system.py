#!/usr/bin/env python
"""
Script de diagnóstico completo del sistema Soptraloc TMS.
Verifica todos los componentes críticos y genera reporte.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
from apps.containers.models import Container
from apps.drivers.models import Driver, Location, Assignment, Alert
from apps.core.models import Company, Vehicle

def check_database():
    """Verifica conexión a base de datos."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Base de datos PostgreSQL: Conectada")
        return True
    except Exception as e:
        print(f"❌ Base de datos: Error - {e}")
        return False

def check_redis():
    """Verifica conexión a Redis."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis: Conectado")
        return True
    except Exception as e:
        print(f"⚠️  Redis: No disponible - {e}")
        print("   Nota: Redis es opcional. Para alertas automáticas, ejecuta: redis-server")
        return False

def check_celery():
    """Verifica que Celery está instalado."""
    try:
        import celery
        print(f"✅ Celery: Instalado (v{celery.__version__})")
        return True
    except ImportError:
        print("❌ Celery: No instalado")
        return False

def check_models():
    """Verifica que los modelos principales funcionan."""
    try:
        # Contar registros
        containers = Container.objects.count()
        drivers = Driver.objects.count()
        locations = Location.objects.count()
        companies = Company.objects.count()
        assignments = Assignment.objects.count()
        alerts = Alert.objects.count()
        
        print("\n📊 Estadísticas del Sistema:")
        print(f"   - Contenedores: {containers}")
        print(f"   - Conductores: {drivers}")
        print(f"   - Ubicaciones: {locations}")
        print(f"   - Empresas: {companies}")
        print(f"   - Asignaciones: {assignments}")
        print(f"   - Alertas: {alerts}")
        
        return True
    except Exception as e:
        print(f"❌ Modelos: Error - {e}")
        return False

def check_users():
    """Verifica usuarios del sistema."""
    try:
        User = get_user_model()
        total_users = User.objects.count()
        admin_users = User.objects.filter(is_superuser=True).count()
        
        print(f"\n👥 Usuarios:")
        print(f"   - Total: {total_users}")
        print(f"   - Administradores: {admin_users}")
        
        if admin_users == 0:
            print("   ⚠️  No hay usuarios administradores. Crear con: python manage.py createsuperuser")
        
        return True
    except Exception as e:
        print(f"❌ Usuarios: Error - {e}")
        return False

def check_migrations():
    """Verifica estado de migraciones."""
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print(f"⚠️  Migraciones pendientes: {len(plan)}")
            print("   Ejecutar: python manage.py migrate")
            return False
        else:
            print("✅ Migraciones: Todas aplicadas")
            return True
    except Exception as e:
        print(f"❌ Migraciones: Error - {e}")
        return False

def check_static_files():
    """Verifica archivos estáticos."""
    try:
        from django.conf import settings
        static_root = settings.STATIC_ROOT
        
        if os.path.exists(static_root):
            print(f"✅ Archivos estáticos: Configurados en {static_root}")
        else:
            print(f"⚠️  Archivos estáticos: Directorio no existe. Ejecutar: python manage.py collectstatic")
        return True
    except Exception as e:
        print(f"❌ Archivos estáticos: Error - {e}")
        return False

def check_environment():
    """Verifica variables de entorno críticas."""
    try:
        from django.conf import settings
        
        print("\n🔧 Configuración:")
        print(f"   - DEBUG: {settings.DEBUG}")
        print(f"   - SECRET_KEY: {'✅ Configurado' if settings.SECRET_KEY and len(settings.SECRET_KEY) > 10 else '⚠️  Débil'}")
        print(f"   - ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"   - MAPBOX_ACCESS_TOKEN: {'✅ Configurado' if hasattr(settings, 'MAPBOX_ACCESS_TOKEN') and settings.MAPBOX_ACCESS_TOKEN else '⚠️  No configurado'}")
        
        return True
    except Exception as e:
        print(f"❌ Configuración: Error - {e}")
        return False

def run_system_check():
    """Ejecuta Django system check."""
    print("\n🔍 Django System Check:")
    try:
        call_command('check', '--deploy')
        return True
    except Exception as e:
        print(f"❌ System Check: Error - {e}")
        return False

def main():
    """Ejecuta todos los checks."""
    print("=" * 60)
    print("🚀 DIAGNÓSTICO COMPLETO - SOPTRALOC TMS")
    print("=" * 60)
    print()
    
    results = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
        'migrations': check_migrations(),
        'models': check_models(),
        'users': check_users(),
        'static': check_static_files(),
        'environment': check_environment(),
    }
    
    run_system_check()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nChecks pasados: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ¡Sistema 100% funcional!")
    elif passed >= total * 0.8:
        print("\n✅ Sistema operativo con advertencias menores")
    else:
        print("\n⚠️  Sistema requiere atención")
    
    print("\n💡 Próximos pasos recomendados:")
    if not results.get('redis'):
        print("   1. Iniciar Redis: redis-server")
        print("   2. Iniciar Celery Worker: celery -A config worker --loglevel=info")
        print("   3. Iniciar Celery Beat: celery -A config beat --loglevel=info")
    
    print("   - Ejecutar servidor: python manage.py runserver")
    print("   - Acceder a: http://localhost:8000/admin/")
    print()

if __name__ == '__main__':
    main()
