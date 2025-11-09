"""
Test for operations panel enhancements
Tests the new endpoints for liberation and programming
"""
import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.containers.models import Container
from apps.programaciones.models import Programacion
from apps.cds.models import CD
from apps.drivers.models import Driver


def test_container_creation():
    """Test creating a container in por_arribar state"""
    print("Testing container creation...")
    
    # Clean up any existing test containers
    Container.objects.filter(container_id='TEST1234567').delete()
    
    container = Container.objects.create(
        container_id='TEST1234567',
        tipo='40',
        nave='TEST VESSEL',
        estado='por_arribar',
        fecha_eta=timezone.now() + timedelta(days=1)
    )
    
    assert container.estado == 'por_arribar'
    assert container.container_id == 'TEST1234567'
    print("✓ Container created successfully")
    return container


def test_container_liberation():
    """Test liberating a container"""
    print("\nTesting container liberation...")
    
    container = Container.objects.filter(container_id='TEST1234567').first()
    if not container:
        container = test_container_creation()
    
    # Change to liberado state
    container.cambiar_estado('liberado', 'test_user')
    
    assert container.estado == 'liberado'
    assert container.fecha_liberacion is not None
    print("✓ Container liberated successfully")
    return container


def test_container_programming():
    """Test programming a liberated container"""
    print("\nTesting container programming...")
    
    container = Container.objects.filter(container_id='TEST1234567').first()
    if not container or container.estado != 'liberado':
        container = test_container_liberation()
    
    # Get or create a test CD
    cd, created = CD.objects.get_or_create(
        nombre='Test CD',
        defaults={
            'codigo': 'TEST_CD',
            'direccion': 'Test Address 123',
            'comuna': 'Test Comuna',
            'tipo': 'cliente',
            'lat': -33.4372,
            'lng': -70.6506,
        }
    )
    
    # Clean up any existing programacion
    Programacion.objects.filter(container=container).delete()
    
    # Create programacion
    fecha_programada = timezone.now() + timedelta(days=2)
    programacion = Programacion.objects.create(
        container=container,
        cd=cd,
        fecha_programada=fecha_programada,
        cliente='Test Cliente',
        direccion_entrega=cd.direccion
    )
    
    # Change container state to programado
    container.cd_entrega = cd
    container.fecha_programacion = timezone.now()
    container.cambiar_estado('programado', 'test_user')
    
    assert container.estado == 'programado'
    assert container.fecha_programacion is not None
    assert programacion.cd == cd
    print("✓ Container programmed successfully")
    return container, programacion


def test_container_assignment():
    """Test assigning a driver to programmed container"""
    print("\nTesting container assignment...")
    
    container, programacion = test_container_programming()
    
    # Get or create a test driver
    driver, created = Driver.objects.get_or_create(
        rut='11111111-1',
        defaults={
            'nombre': 'Test Driver',
            'telefono': '912345678',
            'patente': 'TEST123',
            'activo': True,
            'presente': True
        }
    )
    
    # Assign driver to programacion
    programacion.asignar_conductor(driver, 'test_user')
    
    assert programacion.driver == driver
    assert programacion.fecha_asignacion is not None
    assert container.estado == 'asignado'
    print("✓ Container assigned to driver successfully")
    return container, programacion, driver


def test_full_workflow():
    """Test the complete workflow: liberate -> program -> assign"""
    print("\n" + "="*50)
    print("Testing full workflow: Liberation -> Programming -> Assignment")
    print("="*50)
    
    try:
        # Step 1: Create container
        container = test_container_creation()
        
        # Step 2: Liberate
        container = test_container_liberation()
        
        # Step 3: Program
        container, programacion = test_container_programming()
        
        # Step 4: Assign
        container, programacion, driver = test_container_assignment()
        
        print("\n" + "="*50)
        print("✅ All tests passed successfully!")
        print("="*50)
        print(f"Container: {container.container_id}")
        print(f"Estado: {container.estado}")
        print(f"CD: {programacion.cd.nombre}")
        print(f"Driver: {driver.nombre}")
        print(f"Fecha programación: {container.fecha_programacion}")
        print(f"Fecha asignación: {programacion.fecha_asignacion}")
        
        # Cleanup
        print("\nCleaning up test data...")
        programacion.delete()
        container.delete()
        CD.objects.filter(nombre='Test CD').delete()
        Driver.objects.filter(rut='11111111-1').delete()
        print("✓ Cleanup completed")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_full_workflow()
    exit(0 if success else 1)
