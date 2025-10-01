#!/usr/bin/env python
import os
import sys

# Agregar el directorio al path
sys.path.insert(0, '/workspaces/soptraloc/soptraloc_system')

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_production'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['SECRET_KEY'] = 'test-key-for-diagnosis'

try:
    import django
    print("✅ Django importado correctamente")
    
    django.setup()
    print("✅ Django setup completado")
    
    from django.conf import settings
    print(f"✅ Settings cargados: DEBUG={settings.DEBUG}")
    print(f"✅ INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")
    
    # Intentar importar wsgi
    from config.wsgi import application
    print("✅ WSGI application importada correctamente")
    
    print("\n🎉 TODO FUNCIONA CORRECTAMENTE")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
