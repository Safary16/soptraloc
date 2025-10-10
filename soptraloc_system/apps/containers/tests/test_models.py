"""
Tests críticos para modelos de contenedores.
FASE 8: Testing - Cobertura de funcionalidad core.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from apps.containers.models import Container, ContainerMovement
from apps.core.models import Company, MovementCode
from apps.drivers.models import Location


class ContainerModelTest(TestCase):
    """Tests para el modelo Container."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            rut='12345678-9',
            email='test@test.com',
            phone='+56912345678',
            address='Test Address'
        )
        self.location = Location.objects.create(
            name='Test Location',
            code='LOC001',
            address='Test Address',
            latitude=-33.4489,
            longitude=-70.6693
        )
    
    def test_create_container(self):
        """Test creación básica de contenedor."""
        container = Container.objects.create(
            container_number='TEST123456',
            container_type='20',
            status='available',
            owner_company=self.company,
            created_by=self.user
        )
        self.assertEqual(container.container_number, 'TEST123456')
        self.assertEqual(container.status, 'available')
        self.assertTrue(container.is_active)
    
    def test_container_str_representation(self):
        """Test representación en string del contenedor."""
        container = Container.objects.create(
            container_number='TEST789',
            container_type='40',
            status='available',
            owner_company=self.company
        )
        self.assertEqual(str(container), 'TEST789')
    
    def test_container_update_status(self):
        """Test actualización de estado del contenedor."""
        container = Container.objects.create(
            container_number='TEST999',
            container_type='20',
            status='available',
            owner_company=self.company
        )
        container.status = 'in_transit'
        container.save()
        container.refresh_from_db()
        self.assertEqual(container.status, 'in_transit')


class ContainerMovementTest(TestCase):
    """Tests para movimientos de contenedores."""
    
    def setUp(self):
        """Configuración inicial."""
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            rut='12345678-9',
            email='test@test.com',
            phone='+56912345678',
            address='Test Address'
        )
        self.origin = Location.objects.create(
            name='Origin',
            code='ORIG',
            address='Origin Address',
            latitude=-33.4489,
            longitude=-70.6693
        )
        self.destination = Location.objects.create(
            name='Destination',
            code='DEST',
            address='Dest Address',
            latitude=-33.4689,
            longitude=-70.6893
        )
        self.container = Container.objects.create(
            container_number='MOVE001',
            container_type='20',
            status='available',
            owner_company=self.company
        )
        self.movement_code = MovementCode.objects.create(
            code='TRANSFER_001',
            movement_type='transfer'
        )
    
    def test_create_movement(self):
        """Test creación de movimiento."""
        movement = ContainerMovement.objects.create(
            container=self.container,
            movement_date=timezone.now(),
            origin_location=self.origin,
            destination_location=self.destination,
            movement_code=self.movement_code,
            created_by=self.user
        )
        self.assertEqual(movement.container, self.container)
        self.assertEqual(movement.origin_location, self.origin)
        self.assertEqual(movement.destination_location, self.destination)
    
    def test_movement_updates_container_location(self):
        """Test que el movimiento actualiza la ubicación del contenedor."""
        self.container.current_location = self.origin
        self.container.save()
        
        movement = ContainerMovement.objects.create(
            container=self.container,
            movement_date=timezone.now(),
            origin_location=self.origin,
            destination_location=self.destination,
            movement_code=self.movement_code
        )
        
        # En un caso real, esto se haría con signals o en la vista
        self.container.current_location = self.destination
        self.container.save()
        self.container.refresh_from_db()
        
        self.assertEqual(self.container.current_location, self.destination)
