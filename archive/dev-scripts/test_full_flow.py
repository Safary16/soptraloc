import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.containers.models import Container
from apps.cds.models import CD
from apps.programaciones.models import Programacion
from apps.drivers.models import Driver
from apps.core.services.assignment import AssignmentService


def test_full_flow():
    print("Iniciando prueba end-to-end...")

    # Limpieza previa basada en identificadores únicos de prueba
    Container.objects.filter(container_id="TEST1234567").delete()
    CD.objects.filter(codigo="TCD").delete()
    Driver.objects.filter(rut="12345678-9").delete()

    # 1. Crear datos base
    cd = CD.objects.create(
        nombre="Test CD",
        codigo="TCD",
        activo=True,
        direccion="Dir Test",
        comuna="Comuna Test",
        lat=-33.4372,
        lng=-70.6506,
    )
    driver = Driver.objects.create(nombre="Test Driver", rut="12345678-9", activo=True, presente=True)
    container = Container.objects.create(
        container_id="TEST1234567",
        tipo="20",
        nave="Test Nave",
        estado="por_arribar",
    )

    # 2. Simular Liberación
    container.cambiar_estado("liberado", "test_user")
    print(f"Contenedor {container.container_id} liberado.")

    # 3. Simular Programación
    programacion = Programacion.objects.create(
        container=container,
        cd=cd,
        fecha_programada=datetime.now(),
        cliente="Test Cliente",
    )
    container.cambiar_estado("programado", "test_user")
    print(f"Programación creada para {container.container_id}.")

    # 4. Asignación automática
    resultado = AssignmentService.asignar_mejor_conductor(programacion)
    print(f"Resultado asignación: {resultado.get('success', False)}")

    # 5. Verificar estado
    container.refresh_from_db()
    programacion.refresh_from_db()
    print(f"Estado final: {container.estado}")
    print(f"Conductor asignado: {programacion.driver.nombre if programacion.driver else 'None'}")

    success = container.estado == "asignado" and programacion.driver == driver
    print("✅ Flujo E2E exitoso." if success else "❌ Flujo E2E fallido.")


if __name__ == "__main__":
    test_full_flow()
