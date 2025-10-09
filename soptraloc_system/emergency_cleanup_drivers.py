#!/usr/bin/env python
"""
Script de emergencia para limpiar conductores duplicados/innecesarios
y optimizar queries del dashboard
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.drivers.models import Driver, Assignment
from django.utils import timezone
from datetime import timedelta


def emergency_cleanup():
    """Limpieza de emergencia de conductores"""
    
    print("=" * 80)
    print("🚨 LIMPIEZA DE EMERGENCIA - CONDUCTORES")
    print("=" * 80)
    print()
    
    # 1. Contar conductores
    total_drivers = Driver.objects.count()
    print(f"📊 Conductores totales: {total_drivers}")
    
    if total_drivers <= 100:
        print("✅ Cantidad de conductores normal (≤100). No se requiere limpieza.")
        return
    
    print(f"⚠️  ALERTA: Se detectaron {total_drivers} conductores (excesivo!)")
    print()
    
    # 2. Identificar conductores con asignaciones
    drivers_with_assignments = set(
        Assignment.objects.values_list('driver_id', flat=True).distinct()
    )
    print(f"✅ Conductores con asignaciones: {len(drivers_with_assignments)}")
    
    # 3. Identificar conductores activos recientes (últimos 30 días)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_active = set(
        Driver.objects.filter(
            updated_at__gte=thirty_days_ago
        ).values_list('id', flat=True)
    )
    print(f"✅ Conductores activos (últimos 30 días): {len(recent_active)}")
    
    # 4. Conductores a conservar
    drivers_to_keep = drivers_with_assignments | recent_active
    print(f"✅ Conductores a conservar: {len(drivers_to_keep)}")
    print()
    
    # 5. Conductores a eliminar
    drivers_to_delete = Driver.objects.exclude(id__in=drivers_to_keep)
    count_to_delete = drivers_to_delete.count()
    
    if count_to_delete == 0:
        print("✅ No hay conductores para eliminar")
        return
    
    print(f"🗑️  Conductores a eliminar: {count_to_delete}")
    print()
    
    # Confirmar
    print("⚠️  CONFIRMACIÓN REQUERIDA")
    print(f"Se eliminarán {count_to_delete} conductores sin asignaciones y sin actividad reciente")
    response = input("¿Continuar? (escribir 'SI' en mayúsculas): ")
    
    if response != 'SI':
        print("❌ Operación cancelada")
        return
    
    print()
    print("🔄 Eliminando conductores...")
    
    # Eliminar en lote
    with transaction.atomic():
        deleted_count, _ = drivers_to_delete.delete()
        print(f"✅ Eliminados {deleted_count} conductores")
    
    # Verificar resultado
    remaining = Driver.objects.count()
    print()
    print("=" * 80)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 80)
    print(f"Conductores antes:  {total_drivers}")
    print(f"Conductores después: {remaining}")
    print(f"Eliminados:          {deleted_count}")
    print()


def show_driver_stats():
    """Mostrar estadísticas de conductores"""
    
    print()
    print("=" * 80)
    print("📊 ESTADÍSTICAS DE CONDUCTORES")
    print("=" * 80)
    print()
    
    total = Driver.objects.count()
    active = Driver.objects.filter(is_active=True).count()
    inactive = Driver.objects.filter(is_active=False).count()
    with_assignments = Assignment.objects.values('driver_id').distinct().count()
    
    print(f"Total:                {total}")
    print(f"Activos:              {active}")
    print(f"Inactivos:            {inactive}")
    print(f"Con asignaciones:     {with_assignments}")
    print()
    
    if total > 100:
        print("⚠️  ALERTA: Cantidad excesiva de conductores detectada")
    else:
        print("✅ Cantidad de conductores normal")
    print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        show_driver_stats()
    else:
        show_driver_stats()
        emergency_cleanup()
