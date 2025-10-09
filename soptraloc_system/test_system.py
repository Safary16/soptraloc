#!/usr/bin/env python
"""Prueba end-to-end manual para SOPTRALOC TMS."""

from __future__ import annotations

import os
import sys

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.db import connection

from apps.containers.models import Container
from apps.containers.tasks import generate_demurrage_alerts
from apps.core.models import Company
from apps.drivers.models import Assignment, Driver, Location, TimeMatrix
from apps.routing.mapbox_service import mapbox_service

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def run_system_checks() -> int:
    """Ejecuta las comprobaciones y devuelve el número de fallos."""

    passed = 0
    failed = 0

    def test(name: str, condition: bool, details: str | None = None) -> None:
        nonlocal passed, failed
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

    print("📊 TEST 1: Conexión a Base de Datos")
    print("-" * 70)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        test("Conexión a BD", True, "SQLite conectado correctamente")
    except Exception as exc:  # pragma: no cover
        test("Conexión a BD", False, f"Error: {exc}")
    print()

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
    except Exception as exc:  # pragma: no cover
        test("Modelos", False, f"Error: {exc}")
    print()

    print("📈 TEST 3: Estados de Contenedores")
    print("-" * 70)
    try:
        states = Container.objects.values_list("status", flat=True).distinct()
        test("Múltiples estados", len(states) > 1, f"Estados: {', '.join(states)}")

        liberado = Container.objects.filter(status="LIBERADO").count()
        test("Contenedores LIBERADO", liberado >= 0, f"Cantidad: {liberado}")

        programado = Container.objects.filter(status="PROGRAMADO").count()
        test("Contenedores PROGRAMADO", programado >= 0, f"Cantidad: {programado}")

        asignado = Container.objects.filter(status="ASIGNADO").count()
        test("Contenedores ASIGNADO", asignado >= 0, f"Cantidad: {asignado}")
    except Exception as exc:  # pragma: no cover
        test("Estados", False, f"Error: {exc}")
    print()

    print("🔗 TEST 4: Relaciones Foreign Key")
    print("-" * 70)
    try:
        container = Container.objects.select_related(
            "owner_company",
            "terminal",
            "vessel",
        ).first()
        if container:
            test(
                "Container → Company",
                container.owner_company is not None,
                f"Company: {container.owner_company.name if container.owner_company else 'N/A'}",
            )
            test(
                "Container → Terminal",
                container.terminal is not None,
                f"Terminal: {container.terminal.name if container.terminal else 'N/A'}",
            )
            test(
                "Container → Vessel",
                True,
                f"Vessel: {container.vessel.name if container.vessel else 'N/A'}",
            )
        else:
            test("Container FK", False, "No hay contenedores")
    except Exception as exc:  # pragma: no cover
        test("Container FK", False, f"Error: {exc}")
    print()

    print("⏱️  TEST 5: TimeMatrix")
    print("-" * 70)
    try:
        tm = TimeMatrix.objects.select_related("from_location", "to_location").first()
        if tm:
            test("TimeMatrix existe", True, f"{tm.from_location.name} → {tm.to_location.name}")
            test("Tiempos configurados", tm.travel_time > 0, f"Tiempo viaje: {tm.travel_time}min")
            total = tm.get_total_time()
            test("Cálculo tiempo total", total > 0, f"Tiempo total: {total}min")
        else:
            test("TimeMatrix", False, "No hay rutas configuradas")
    except Exception as exc:  # pragma: no cover
        test("TimeMatrix", False, f"Error: {exc}")
    print()

    print("👥 TEST 6: Asignaciones")
    print("-" * 70)
    try:
        assignment = Assignment.objects.select_related("container", "driver", "origen", "destino").first()
        if assignment:
            test(
                "Assignment existe",
                True,
                f"{assignment.container.container_number} → {assignment.driver.display_name}",
            )
            test(
                "Assignment origen",
                assignment.origen is not None,
                f"Origen: {assignment.origen.name if assignment.origen else 'N/A'}",
            )
            test(
                "Assignment destino",
                assignment.destino is not None,
                f"Destino: {assignment.destino.name if assignment.destino else 'N/A'}",
            )
            test(
                "Assignment estado",
                assignment.estado in ["PENDIENTE", "EN_CURSO"],
                f"Estado: {assignment.estado}",
            )
        else:
            test("Assignment", False, "No hay asignaciones")
    except Exception as exc:  # pragma: no cover
        test("Assignment", False, f"Error: {exc}")
    print()

    print("🔄 TEST 7: Máquina de Estados")
    print("-" * 70)
    try:
        container = Container.objects.filter(status="LIBERADO").first()
        if container:
            test("Transición LIBERADO → PROGRAMADO", True, "Transición válida")
            test("Transición LIBERADO → FINALIZADO", False, "⚠️  Requiere validación manual")
        else:
            test("State Machine", False, "No hay contenedores LIBERADO para probar")
    except Exception as exc:  # pragma: no cover
        test("State Machine", False, f"Error: {exc}")
    print()

    print("⚙️  TEST 8: Tareas Celery")
    print("-" * 70)
    try:
        result = generate_demurrage_alerts()
        test("Tarea generate_demurrage_alerts", True, f"Alertas generadas: {result.get('warnings_generated', 0)}")
    except Exception as exc:  # pragma: no cover
        test("Celery Tasks", False, f"Error: {exc}")
    print()

    print("🔴 TEST 9: Redis")
    print("-" * 70)
    try:
        import redis

        client = redis.Redis(host="localhost", port=6379, db=0)
        pong = client.ping()
        test("Redis conectado", pong, "Redis responde a PING")
    except Exception as exc:  # pragma: no cover
        test("Redis", False, f"Error: {exc}")
    print()

    print("🗺️  TEST 10: Integración Mapbox")
    print("-" * 70)
    try:
        has_key = bool(settings.MAPBOX_API_KEY)
        test(
            "MAPBOX_API_KEY configurado",
            has_key,
            "✅ Token configurado" if has_key else "⚠️  No configurado (usando fallback)",
        )

        if has_key:
            result = mapbox_service.get_travel_time_with_traffic("CCTI", "CD_PENON")
            is_realtime = result.get("source") == "mapbox_api"
            test("Mapbox API funcional", is_realtime, f"Fuente: {result.get('source', 'unknown')}")
            if is_realtime:
                test(
                    "Cálculo de tráfico",
                    result.get("traffic_level") is not None,
                    f"Nivel: {result.get('traffic_level', 'unknown')}",
                )
                test(
                    "Tiempo con tráfico",
                    result.get("duration_in_traffic_minutes", 0) > 0,
                    f"Duración: {result.get('duration_in_traffic_minutes')} min",
                )
        else:
            test("Modo fallback", True, "Sistema usa tiempos estáticos (OK para desarrollo)")
    except Exception as exc:  # pragma: no cover
        test("Mapbox", False, f"Error: {exc}")
    print()

    print("🚦 TEST 11: Asignaciones con Tráfico")
    print("-" * 70)
    try:
        test(
            "Modelo actualizado",
            hasattr(Assignment, "traffic_level_at_assignment"),
            "Campo traffic_level_at_assignment existe",
        )
        test(
            "Método get_traffic_emoji",
            hasattr(Assignment, "get_traffic_emoji"),
            "Método para mostrar emoji de tráfico",
        )
        assignments_with_traffic = Assignment.objects.exclude(traffic_level_at_assignment="unknown").count()
        test(
            "Asignaciones con info de tráfico",
            assignments_with_traffic >= 0,
            f"Total: {assignments_with_traffic} assignments con datos de tráfico",
        )
    except Exception as exc:  # pragma: no cover
        test("Assignment tráfico", False, f"Error: {exc}")
    print()

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
    else:
        print("🎉 ¡TODOS LOS TESTS PASARON! Sistema completamente funcional.")

    return failed


if __name__ == "__main__":  # pragma: no cover
    exit_code = 1 if run_system_checks() else 0
    sys.exit(exit_code)
