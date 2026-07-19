from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.drivers.models import Driver
from apps.containers.models import Container
from apps.notifications.models import Notification
from apps.cds.models import CD
from .models import Programacion
from unittest.mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate
from .views import ProgramacionViewSet


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
    
    def test_crear_programacion_actualiza_container_a_programado(self):
        """Creating a schedule establishes the container's programmed state."""
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'programado')

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


class ProgramacionArriboTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='arribo_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='Arribo Driver', user=self.user, patente='ARR123',
        )
        self.cd = CD.objects.create(
            nombre='CD Arribo', codigo='ARR-CD', direccion='Destino', comuna='Santiago',
            lat=-33.450000, lng=-70.650000,
        )
        self.container = Container.objects.create(
            container_id='ARRI1234567', estado='asignado', cliente='Cliente'
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='Cliente', fecha_programada=timezone.now() + timedelta(hours=1),
        )
        self.container.estado = 'en_ruta'
        self.container.fecha_inicio_ruta = timezone.now() - timedelta(minutes=10)
        self.container.save(update_fields=['estado', 'fecha_inicio_ruta', 'updated_at'])
        self.programacion.fecha_inicio_ruta = self.container.fecha_inicio_ruta
        self.programacion.save(update_fields=['fecha_inicio_ruta', 'updated_at'])
        self.factory = APIRequestFactory()

    def _post(self, action, data):
        request = self.factory.post('/', data, format='json')
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': action})
        return view(request, pk=self.programacion.pk)

    def test_manual_arrival_requires_and_persists_gps(self):
        missing = self._post('notificar_arribo', {})
        self.assertEqual(missing.status_code, 400)

        response = self._post('notificar_arribo', {'lat': -33.45, 'lng': -70.65})
        self.assertEqual(response.status_code, 200)
        self.programacion.refresh_from_db()
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'entregado')
        self.assertIsNotNone(self.programacion.fecha_arribo_cd)
        self.assertEqual(self.programacion.origen_arribo, 'manual')
        self.assertEqual(float(self.programacion.gps_arribo_lat), -33.45)
        self.assertEqual(float(self.programacion.gps_arribo_lng), -70.65)

    def test_position_inside_configured_geofence_registers_arrival(self):
        self.cd.geocerca_radio_m = 200
        self.cd.save(update_fields=['geocerca_radio_m', 'updated_at'])
        with patch('apps.notifications.services.NotificationService.actualizar_eta') as eta:
            response = self._post('actualizar_posicion', {'lat': -33.45, 'lng': -70.65})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['arribo_automatico'])
        eta.assert_not_called()
        self.programacion.refresh_from_db()
        self.assertEqual(self.programacion.origen_arribo, 'geocerca')
        self.assertIsNotNone(self.programacion.fecha_arribo_cd)

    def test_geofence_is_inactive_without_explicit_radius(self):
        self.assertFalse(self.cd.contiene_en_geocerca(-33.45, -70.65))

    def test_driver_cannot_register_another_drivers_arrival(self):
        other_user = User.objects.create_user(username='other_arribo', password='***')
        request = self.factory.post('/', {'lat': -33.45, 'lng': -70.65}, format='json')
        force_authenticate(request, user=other_user)
        view = ProgramacionViewSet.as_view({'post': 'notificar_arribo'})

        response = view(request, pk=self.programacion.pk)

        self.assertEqual(response.status_code, 403)
        self.programacion.refresh_from_db()
        self.assertIsNone(self.programacion.fecha_arribo_cd)

    def test_repeated_manual_arrival_is_idempotent(self):
        first = self._post('notificar_arribo', {'lat': -33.45, 'lng': -70.65})
        second = self._post('notificar_arribo', {'lat': -33.46, 'lng': -70.66})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['ya_registrado'])
        self.programacion.refresh_from_db()
        self.assertEqual(float(self.programacion.gps_arribo_lat), -33.45)
        self.assertEqual(float(self.programacion.gps_arribo_lng), -70.65)
