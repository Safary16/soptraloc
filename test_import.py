import os
import sys
import django

sys.path.append('/workspaces/soptraloc')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.importers.embarque import EmbarqueImporter
from apps.containers.importers.liberacion import LiberacionImporter
from apps.containers.importers.programacion import ProgramacionImporter
from apps.containers.models import Container

print("\n" + "="*80)
print("TEST DE IMPORTACIÓN DE ARCHIVOS EXCEL REALES")
print("="*80)

# 1. IMPORTAR EMBARQUE
print("\n📦 1. IMPORTANDO EMBARQUE/NAVE...")
print("-" * 80)
embarque_file = 'apps/APL CHARLESTON ETA 26-09 SERRANO CCTI.xlsx'

if os.path.exists(embarque_file):
    importer = EmbarqueImporter(embarque_file, 'test_user')
    resultados = importer.procesar()
    
    print(f"\n✅ Resultado Embarque:")
    print(f"   - Creados: {resultados['creados']}")
    print(f"   - Actualizados: {resultados['actualizados']}")
    print(f"   - Errores: {resultados['errores']}")
    
    if resultados['detalles'][:3]:
        print(f"\n   Primeros 3 registros:")
        for det in resultados['detalles'][:3]:
            print(f"      {det}")
else:
    print("   ❌ Archivo no encontrado")

# Verificar containers creados
total_containers = Container.objects.count()
print(f"\n   Total contenedores en sistema: {total_containers}")

# Mostrar algunos
if total_containers > 0:
    print(f"\n   Muestra de contenedores:")
    for cont in Container.objects.all()[:3]:
        print(f"      - {cont.container_id}: {cont.nave} | {cont.tipo} | Peso: {cont.peso_carga} kg | ETA: {cont.fecha_eta}")

# 2. IMPORTAR LIBERACIÓN
print("\n\n�� 2. IMPORTANDO LIBERACIÓN...")
print("-" * 80)
liberacion_file = 'apps/liberacion.xlsx'

if os.path.exists(liberacion_file):
    importer = LiberacionImporter(liberacion_file, 'test_user')
    resultados = importer.procesar()
    
    print(f"\n✅ Resultado Liberación:")
    print(f"   - Liberados: {resultados['liberados']}")
    print(f"   - No encontrados: {resultados['no_encontrados']}")
    print(f"   - Errores: {resultados['errores']}")
    
    if resultados['detalles'][:3]:
        print(f"\n   Primeros 3 registros:")
        for det in resultados['detalles'][:3]:
            print(f"      {det}")
else:
    print("   ❌ Archivo no encontrado")

# Verificar liberados
liberados = Container.objects.filter(estado='liberado').count()
print(f"\n   Contenedores liberados: {liberados}")

# 3. IMPORTAR PROGRAMACIÓN
print("\n\n📅 3. IMPORTANDO PROGRAMACIÓN...")
print("-" * 80)
programacion_file = 'apps/programacion.xlsx'

if os.path.exists(programacion_file):
    importer = ProgramacionImporter(programacion_file, 'test_user')
    resultados = importer.procesar()
    
    print(f"\n✅ Resultado Programación:")
    print(f"   - Programados: {resultados['programados']}")
    print(f"   - No encontrados: {resultados['no_encontrados']}")
    print(f"   - CD no encontrado: {resultados['cd_no_encontrado']}")
    print(f"   - Errores: {resultados['errores']}")
    print(f"   - Alertas generadas: {resultados['alertas_generadas']}")
    
    if resultados['detalles'][:3]:
        print(f"\n   Primeros 3 registros:")
        for det in resultados['detalles'][:3]:
            print(f"      {det}")
else:
    print("   ❌ Archivo no encontrado")

# Verificar programados
programados = Container.objects.filter(estado='programado').count()
print(f"\n   Contenedores programados: {programados}")

print("\n" + "="*80)
print("TEST COMPLETADO")
print("="*80)

