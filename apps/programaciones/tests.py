from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.drivers.models import Driver
from apps.containers.models import Container
from apps.notifications.models import Notification
from apps.cds.models import CD
from .models import Programacion


class ProgramacionAsignacionTests(TestCase):
    """Tests for driver assignment and notifications"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user and driver
        self.user = User.objects.create_user(
            username='test_driver',
            password='test123'
        )
        self.driver = Driver.objects.create(
            nombre='Test Driver',
            rut='12345678-9',
            user=self.user,
            num_entregas_dia=0,
            max_entregas_dia=3
        )
        
        # Create test CD
        self.cd = CD.objects.create(
            nombre='Test CD',
            codigo='TEST-CD',
            tipo='cliente',
            direccion='Test Address',
            lat=-33.4569,
            lng=-70.6483
        )
        
        # Create test container
        self.container = Container.objects.create(
            container_id='TEST123',
            cliente='Test Cliente',
            estado='liberado'
        )
        
        # Create test programacion
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            cliente='Test Cliente',
            fecha_programada=timezone.now() + timedelta(hours=24)
        )
    
    def test_asignar_conductor_creates_notification(self):
        """Test that assigning a driver creates a notification"""
        # Verify no notifications exist before assignment
        self.assertEqual(Notification.objects.count(), 0)
        
        # Assign driver
        self.programacion.asignar_conductor(self.driver)
        
        # Verify notification was created
        notifications = Notification.objects.filter(
            driver=self.driver,
            programacion=self.programacion,
            tipo='asignacion'
        )
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.prioridad, 'media')
        self.assertIn('TEST123', notification.titulo)
        self.assertIn('Test Cliente', notification.mensaje)
    
    def test_asignar_conductor_updates_container_estado(self):
        """Test that assigning a driver updates container state"""
        self.programacion.asignar_conductor(self.driver)
        
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'asignado')
    
    def test_asignar_conductor_increments_entregas_dia(self):
        """Test that assigning a driver increments daily deliveries"""
        initial_count = self.driver.num_entregas_dia
        
        self.programacion.asignar_conductor(self.driver)
        
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.num_entregas_dia, initial_count + 1)
    
    def test_asignar_conductor_sets_fecha_asignacion(self):
        """Test that assigning a driver sets assignment date"""
        self.programacion.asignar_conductor(self.driver)
        
        self.programacion.refresh_from_db()
        self.assertIsNotNone(self.programacion.fecha_asignacion)
        self.assertEqual(self.programacion.driver, self.driver)
