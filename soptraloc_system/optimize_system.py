#!/usr/bin/env python
"""
Script de optimización y limpieza del sistema SOPTRALOC TMS
Optimiza base de datos, limpia logs y valida integridad
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
from apps.drivers.models import Driver, Assignment, Alert
from apps.containers.models import Container
from datetime import timedelta
from django.utils import timezone

print("\n" + "="*70)
print("🔧 OPTIMIZACIÓN DEL SISTEMA SOPTRALOC TMS")
print("="*70 + "\n")

# 1. Limpiar alertas antiguas resueltas
print("📋 1. Limpiando alertas antiguas...")
fecha_limite = timezone.now() - timedelta(days=30)
alertas_eliminadas = Alert.objects.filter(
    is_active=False,
    fecha_resolucion__lt=fecha_limite
).delete()[0]
print(f"   ✅ {alertas_eliminadas} alertas antiguas eliminadas\n")

# 2. Limpiar asignaciones completadas antiguas (más de 60 días)
print("📦 2. Limpiando asignaciones completadas antiguas...")
fecha_limite_asignaciones = timezone.now() - timedelta(days=60)
asignaciones_eliminadas = Assignment.objects.filter(
    estado='COMPLETADA',
    fecha_completada__lt=fecha_limite_asignaciones
).delete()[0]
print(f"   ✅ {asignaciones_eliminadas} asignaciones antiguas eliminadas\n")

# 3. Actualizar conductores inactivos
print("👥 3. Actualizando estado de conductores...")
conductores_actualizados = Driver.objects.filter(
    is_active=True,
    contenedor_asignado__isnull=True,
    estado='OPERATIVO'
).count()
print(f"   ℹ️  {conductores_actualizados} conductores operativos sin asignación\n")

# 4. Verificar integridad de datos
print("🔍 4. Verificando integridad de datos...")

# Contenedores sin empresa
contenedores_sin_empresa = Container.objects.filter(owner_company__isnull=True).count()
if contenedores_sin_empresa > 0:
    print(f"   ⚠️  {contenedores_sin_empresa} contenedores sin empresa")
else:
    print(f"   ✅ Todos los contenedores tienen empresa asignada")

# Asignaciones sin conductor
asignaciones_sin_conductor = Assignment.objects.filter(driver__isnull=True).count()
if asignaciones_sin_conductor > 0:
    print(f"   ⚠️  {asignaciones_sin_conductor} asignaciones sin conductor")
else:
    print(f"   ✅ Todas las asignaciones tienen conductor")

# Asignaciones sin contenedor
asignaciones_sin_contenedor = Assignment.objects.filter(container__isnull=True).count()
if asignaciones_sin_contenedor > 0:
    print(f"   ⚠️  {asignaciones_sin_contenedor} asignaciones sin contenedor")
else:
    print(f"   ✅ Todas las asignaciones tienen contenedor\n")

# 5. Optimizar base de datos SQLite
print("💾 5. Optimizando base de datos...")
with connection.cursor() as cursor:
    cursor.execute("VACUUM;")
    cursor.execute("ANALYZE;")
print("   ✅ Base de datos optimizada\n")

# 6. Limpiar caché
print("🗑️  6. Limpiando caché...")
try:
    call_command('clear_cache', verbosity=0)
    print("   ✅ Caché limpiada\n")
except:
    print("   ℹ️  No hay sistema de caché configurado\n")

# 7. Recolectar archivos estáticos
print("📦 7. Verificando archivos estáticos...")
try:
    static_files = os.path.exists('staticfiles')
    if static_files:
        print("   ✅ Archivos estáticos presentes\n")
    else:
        print("   ℹ️  No hay directorio staticfiles (ejecutar collectstatic en producción)\n")
except Exception as e:
    print(f"   ⚠️  Error verificando estáticos: {e}\n")

# 8. Limpiar logs antiguos
print("📄 8. Limpiando logs antiguos...")
logs_eliminados = 0
for log_file in ['celery_worker.log', 'celery_beat.log', 'nohup.out']:
    log_path = os.path.join(os.path.dirname(__file__), log_file)
    if os.path.exists(log_path):
        file_size = os.path.getsize(log_path)
        if file_size > 10 * 1024 * 1024:  # > 10MB
            with open(log_path, 'w') as f:
                f.write(f"# Log limpiado el {timezone.now()}\n")
            logs_eliminados += 1
if logs_eliminados > 0:
    print(f"   ✅ {logs_eliminados} logs grandes limpiados\n")
else:
    print(f"   ✅ Logs en tamaño razonable\n")

# Resumen final
print("="*70)
print("📊 RESUMEN DE OPTIMIZACIÓN")
print("="*70 + "\n")

print(f"Conductores activos: {Driver.objects.filter(is_active=True).count()}")
print(f"Contenedores totales: {Container.objects.count()}")
print(f"Asignaciones activas: {Assignment.objects.filter(estado__in=['PENDIENTE', 'EN_CURSO']).count()}")
print(f"Alertas activas: {Alert.objects.filter(is_active=True).count()}")

print("\n✅ Optimización completada exitosamente!\n")
print("="*70 + "\n")
