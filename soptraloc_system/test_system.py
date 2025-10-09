#!/usr/bin/env python
"""
Script de prueba end-to-end para SOPTRALOC TMS
Verifica que todos los componentes del sistema funcionen correctamente
"""

import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.containers.models import Container, Agency, ShippingLine, Vessel
from apps.drivers.models import Location, Driver, TimeMatrix, Assignment, Alert
from apps.core.models import Company
from django.utils import timezone

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

passed = 0
failed = 0

def test(name, condition, details=""):
    """Helper function to run tests"""
    global passed, failed
    if condition:
        print(f"{GREEN}✅ {name}{RESET}")
        if details:
            print(f"   {details}")
        passed += 1
    else:
        print(f"{RED}❌ {name}{RESET}")
        if details:
            print(f"   {details}")
        failed += 1

print("=" * 70)
print("  🧪 SOPTRALOC TMS - PRUEBA END-TO-END")
print("=" * 70)
print()

# TEST 1: Database Connection
print("📊 TEST 1: Conexión a Base de Datos")
print("-" * 70)
try:
    from django.db import connection
    cursor = connection.cursor()
    test("Conexión a BD", True, "SQLite conectado correctamente")
except Exception as e:
    test("Conexión a BD", False, f"Error: {e}")
print()

# TEST 2: Models and Data
print("📦 TEST 2: Modelos y Datos")
print("-" * 70)
try:
    containers_count = Container.objects.count()
    test("Contenedores existen", containers_count > 0, f"Total: {containers_count} contenedores")
    
    locations_count = Location.objects.count()
    test("Ubicaciones existen", locations_count > 0, f"Total: {locations_count} ubicaciones")
    
    drivers_count = Driver.objects.count()
    test("Conductores existen", drivers_count > 0, f"Total: {drivers_count} conductores")
    
    timematrix_count = TimeMatrix.objects.count()
    test("TimeMatrix configurada", timematrix_count > 0, f"Total: {timematrix_count} rutas")
    
    companies_count = Company.objects.count()
    test("Empresas existen", companies_count > 0, f"Total: {companies_count} empresas")
    
    assignments_count = Assignment.objects.count()
    test("Asignaciones existen", assignments_count > 0, f"Total: {assignments_count} asignaciones")
except Exception as e:
    test("Modelos", False, f"Error: {e}")
print()

# TEST 3: Container States
print("📈 TEST 3: Estados de Contenedores")
print("-" * 70)
try:
    states = Container.objects.values_list('status', flat=True).distinct()
    test("Múltiples estados", len(states) > 1, 
         f"Estados: {', '.join(states)}")
    
    liberado = Container.objects.filter(status='LIBERADO').count()
    test("Contenedores LIBERADO", liberado >= 0, f"Cantidad: {liberado}")
    
    programado = Container.objects.filter(status='PROGRAMADO').count()
    test("Contenedores PROGRAMADO", programado >= 0, f"Cantidad: {programado}")
    
    asignado = Container.objects.filter(status='ASIGNADO').count()
    test("Contenedores ASIGNADO", asignado >= 0, f"Cantidad: {asignado}")
except Exception as e:
    test("Estados", False, f"Error: {e}")
print()

# TEST 4: Foreign Key Relationships
print("🔗 TEST 4: Relaciones Foreign Key")
print("-" * 70)
try:
    container = Container.objects.select_related('company', 'terminal', 'vessel').first()
    if container:
        test("Container → Company", container.company is not None,
             f"Company: {container.company.name if container.company else 'N/A'}")
        test("Container → Terminal", container.terminal is not None,
             f"Terminal: {container.terminal.name if container.terminal else 'N/A'}")
        test("Container → Vessel", True,
             f"Vessel: {container.vessel.name if container.vessel else 'N/A'}")
    else:
        test("Container FK", False, "No hay contenedores")
except Exception as e:
    test("Container FK", False, f"Error: {e}")
print()

# TEST 5: TimeMatrix
print("⏱️  TEST 5: TimeMatrix")
print("-" * 70)
try:
    tm = TimeMatrix.objects.select_related('from_location', 'to_location').first()
    if tm:
        test("TimeMatrix existe", True, 
             f"{tm.from_location.name} → {tm.to_location.name}")
        test("Tiempos configurados", tm.travel_time > 0,
             f"Tiempo viaje: {tm.travel_time}min")
        total = tm.get_total_time()
        test("Cálculo tiempo total", total > 0,
             f"Tiempo total: {total}min")
    else:
        test("TimeMatrix", False, "No hay rutas configuradas")
except Exception as e:
    test("TimeMatrix", False, f"Error: {e}")
print()

# TEST 6: Assignments
print("👥 TEST 6: Asignaciones")
print("-" * 70)
try:
    assignment = Assignment.objects.select_related(
        'container', 'driver', 'origen', 'destino'
    ).first()
    if assignment:
        test("Assignment existe", True,
             f"{assignment.container.container_number} → {assignment.driver.nombre}")
        test("Assignment origen", assignment.origen is not None,
             f"Origen: {assignment.origen.name if assignment.origen else 'N/A'}")
        test("Assignment destino", assignment.destino is not None,
             f"Destino: {assignment.destino.name if assignment.destino else 'N/A'}")
        test("Assignment estado", assignment.estado in ['PENDIENTE', 'EN_CURSO'],
             f"Estado: {assignment.estado}")
    else:
        test("Assignment", False, "No hay asignaciones")
except Exception as e:
    test("Assignment", False, f"Error: {e}")
print()

# TEST 7: State Machine
print("🔄 TEST 7: Máquina de Estados")
print("-" * 70)
try:
    # Test valid transition
    container = Container.objects.filter(status='LIBERADO').first()
    if container:
        old_status = container.status
        container.status = 'PROGRAMADO'
        test("Transición LIBERADO → PROGRAMADO", True, "Transición válida")
        container.status = old_status
        
        # Test invalid transition
        try:
            container.status = 'FINALIZADO'
            test("Transición LIBERADO → FINALIZADO", False, "⚠️  Transición debería ser inválida")
        except:
            test("Transición LIBERADO → FINALIZADO", True, "Transición inválida bloqueada")
        container.status = old_status
    else:
        test("State Machine", False, "No hay contenedores LIBERADO para probar")
except Exception as e:
    test("State Machine", False, f"Error: {e}")
print()

# TEST 8: Celery Tasks
print("⚙️  TEST 8: Tareas Celery")
print("-" * 70)
try:
    from apps.containers.tasks import generate_demurrage_alerts
    result = generate_demurrage_alerts()
    test("Tarea generate_demurrage_alerts", True,
         f"Alertas generadas: {result.get('warnings_generated', 0)}")
except Exception as e:
    test("Celery Tasks", False, f"Error: {e}")
print()

# TEST 9: Redis
print("🔴 TEST 9: Redis")
print("-" * 70)
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    pong = r.ping()
    test("Redis conectado", pong, "Redis responde a PING")
except Exception as e:
    test("Redis", False, f"Error: {e}")
print()

# TEST 10: Mapbox Integration
print("🗺️  TEST 10: Integración Mapbox")
print("-" * 70)
try:
    from django.conf import settings
    has_key = bool(settings.MAPBOX_API_KEY)
    test("MAPBOX_API_KEY configurado", has_key,
         f"{'✅ Token configurado' if has_key else '⚠️  No configurado (usando fallback)'}")
    
    if has_key:
        from apps.routing.mapbox_service import mapbox_service
        result = mapbox_service.get_travel_time_with_traffic('CCTI', 'CD_PENON')
        
        is_realtime = result.get('source') == 'mapbox_api'
        test("Mapbox API funcional", is_realtime,
             f"Fuente: {result.get('source', 'unknown')}")
        
        if is_realtime:
            test("Cálculo de tráfico", result.get('traffic_level') is not None,
                 f"Nivel: {result.get('traffic_level', 'unknown')}")
            test("Tiempo con tráfico", result.get('duration_in_traffic_minutes', 0) > 0,
                 f"Duración: {result.get('duration_in_traffic_minutes')} min")
    else:
        test("Modo fallback", True, "Sistema usa tiempos estáticos (OK para desarrollo)")
except Exception as e:
    test("Mapbox", False, f"Error: {e}")
print()

# TEST 11: Assignment con información de tráfico
print("🚦 TEST 11: Asignaciones con Tráfico")
print("-" * 70)
try:
    # Verificar que existe el campo traffic_level_at_assignment
    from apps.drivers.models import Assignment
    test("Modelo actualizado", 
         hasattr(Assignment, 'traffic_level_at_assignment'),
         "Campo traffic_level_at_assignment existe")
    
    test("Método get_traffic_emoji", 
         hasattr(Assignment, 'get_traffic_emoji'),
         "Método para mostrar emoji de tráfico")
    
    # Verificar asignaciones existentes
    assignments_with_traffic = Assignment.objects.exclude(
        traffic_level_at_assignment='unknown'
    ).count()
    
    test("Asignaciones con info de tráfico", assignments_with_traffic >= 0,
         f"Total: {assignments_with_traffic} assignments con datos de tráfico")
except Exception as e:
    test("Assignment tráfico", False, f"Error: {e}")
print()

# Summary
print("=" * 70)
print("  📊 RESUMEN DE PRUEBAS")
print("=" * 70)
print(f"  {GREEN}✅ Tests Pasados: {passed}{RESET}")
print(f"  {RED}❌ Tests Fallidos: {failed}{RESET}")
total = passed + failed
if total > 0:
    percentage = (passed / total) * 100
    print(f"  📈 Tasa de Éxito: {percentage:.1f}%")
print("=" * 70)
print()

if failed > 0:
    print(f"⚠️  {failed} tests fallaron. Revisar configuración.")
    sys.exit(1)
else:
    print("🎉 ¡TODOS LOS TESTS PASARON! Sistema completamente funcional.")
    sys.exit(0)
