import os
import sys
import django

# Configurar Django
sys.path.append('/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container

print("🔍 DIAGNÓSTICO: ¿POR QUÉ NO APARECEN CONTENEDORES?")
print("=" * 60)

total = Container.objects.count()
activos = Container.objects.filter(is_active=True).count()
inactivos = Container.objects.filter(is_active=False).count()

print(f"📦 Total contenedores en DB: {total}")
print(f"✅ Contenedores activos (is_active=True): {activos}")
print(f"❌ Contenedores inactivos (is_active=False): {inactivos}")

print(f"\n🎯 PROBLEMA IDENTIFICADO:")
if total > 0 and activos == 0:
    print("❌ TODOS LOS CONTENEDORES ESTÁN MARCADOS COMO INACTIVOS!")
    print("   La API/ViewSet filtra por is_active=True, por eso no aparecen.")
elif activos > 0:
    print("✅ Hay contenedores activos, el problema puede estar en otro lado.")
else:
    print("❌ NO HAY CONTENEDORES EN LA BASE DE DATOS.")

print(f"\n📊 MUESTRA DE CONTENEDORES:")
for i, c in enumerate(Container.objects.all()[:5], 1):
    status_icon = '✅' if c.is_active else '❌'
    print(f"  {i}. {c.container_number} - is_active: {c.is_active} {status_icon}")