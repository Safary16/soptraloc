from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Driver, DriverLocation


class DriverAuthenticationTests(TestCase):
    """Tests for driver authentication system"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a test user and driver
        self.user = User.objects.create_user(
            username='test_driver',
            password='test123'
        )
        self.driver = Driver.objects.create(
            nombre='Test Driver',
            rut='12345678-9',
            telefono='123456789',
            user=self.user
        )
    
    def test_driver_login_page_loads(self):
        """Test that driver login page loads correctly"""
        response = self.client.get(reverse('driver_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SoptraLoc TMS')
        self.assertContains(response, 'Acceso para Conductores')
    
    def test_driver_can_login(self):
        """Test that driver can login with correct credentials"""
        response = self.client.post(reverse('driver_login'), {
            'username': 'test_driver',
            'password': 'test123'
        })
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('driver_dashboard')))
    
    def test_driver_cannot_login_with_wrong_password(self):
        """Test that login fails with wrong password"""
        response = self.client.post(reverse('driver_login'), {
            'username': 'test_driver',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('driver_dashboard'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue('login' in response.url)
    
    def test_dashboard_loads_for_authenticated_driver(self):
        """Test that dashboard loads for authenticated driver"""
        self.client.login(username='test_driver', password='test123')
        response = self.client.get(reverse('driver_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Driver')
        self.assertContains(response, 'Mis Entregas')
    
    def test_driver_logout(self):
        """Test that driver can logout"""
        self.client.login(username='test_driver', password='test123')
        response = self.client.get(reverse('driver_logout'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('driver_login')))


class DriverGPSTrackingTests(APITestCase):
    """Tests for GPS tracking functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user and driver
        self.user = User.objects.create_user(
            username='gps_driver',
            password='test123'
        )
        self.driver = Driver.objects.create(
            nombre='GPS Driver',
            rut='98765432-1',
            user=self.user
        )
    
    def test_track_location_requires_authentication(self):
        """Test that tracking location requires authentication"""
        url = reverse('driver-track-location', kwargs={'pk': self.driver.id})
        response = self.client.post(url, {
            'lat': -33.4569,
            'lng': -70.6483,
            'accuracy': 10.5
        }, format='json')
        # Should return 403 (Forbidden) since not authenticated
        self.assertEqual(response.status_code, 403)
    
    def test_track_location_with_authentication(self):
        """Test GPS tracking with authentication"""
        self.client.force_authenticate(user=self.user)
        url = reverse('driver-track-location', kwargs={'pk': self.driver.id})
        
        response = self.client.post(url, {
            'lat': -33.4569,
            'lng': -70.6483,
            'accuracy': 10.5
        }, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Verify location was saved
        self.driver.refresh_from_db()
        self.assertIsNotNone(self.driver.ultima_posicion_lat)
        self.assertIsNotNone(self.driver.ultima_posicion_lng)
        self.assertEqual(float(self.driver.ultima_posicion_lat), -33.4569)
        self.assertEqual(float(self.driver.ultima_posicion_lng), -70.6483)
    
    def test_location_history_is_created(self):
        """Test that location history is created when tracking"""
        self.client.force_authenticate(user=self.user)
        url = reverse('driver-track-location', kwargs={'pk': self.driver.id})
        
        # Track location
        self.client.post(url, {
            'lat': -33.4569,
            'lng': -70.6483,
            'accuracy': 10.5
        }, format='json')
        
        # Verify history record was created
        locations = DriverLocation.objects.filter(driver=self.driver)
        self.assertEqual(locations.count(), 1)
        
        location = locations.first()
        self.assertEqual(float(location.lat), -33.4569)
        self.assertEqual(float(location.lng), -70.6483)
        self.assertEqual(location.accuracy, 10.5)
    
    def test_active_locations_returns_recent_drivers(self):
        """Test that active_locations returns drivers with recent GPS data"""
        # Set recent location
        self.driver.ultima_posicion_lat = -33.4569
        self.driver.ultima_posicion_lng = -70.6483
        self.driver.ultima_actualizacion_posicion = timezone.now()
        self.driver.save()
        
        url = reverse('driver-active-locations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'GPS Driver')
    
    def test_active_locations_excludes_old_data(self):
        """Test that active_locations excludes drivers with old GPS data"""
        # Set old location (more than 30 minutes ago)
        self.driver.ultima_posicion_lat = -33.4569
        self.driver.ultima_posicion_lng = -70.6483
        self.driver.ultima_actualizacion_posicion = timezone.now() - timedelta(minutes=35)
        self.driver.save()
        
        url = reverse('driver-active-locations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
    
    def test_driver_cannot_track_other_drivers(self):
        """Test that driver cannot update location for other drivers"""
        # Create another driver
        other_user = User.objects.create_user(username='other_driver', password='test123')
        other_driver = Driver.objects.create(nombre='Other Driver', user=other_user)
        
        # Try to track other driver's location
        self.client.force_authenticate(user=self.user)
        url = reverse('driver-track-location', kwargs={'pk': other_driver.id})
        
        response = self.client.post(url, {
            'lat': -33.4569,
            'lng': -70.6483
        }, format='json')
        
        self.assertEqual(response.status_code, 403)


class DriverModelTests(TestCase):
    """Tests for Driver model"""
    
    def test_driver_availability(self):
        """Test driver availability calculation"""
        driver = Driver.objects.create(
            nombre='Available Driver',
            activo=True,
            presente=True,
            num_entregas_dia=2,
            max_entregas_dia=3
        )
        self.assertTrue(driver.esta_disponible)
    
    def test_driver_not_available_when_max_reached(self):
        """Test driver is not available when max deliveries reached"""
        driver = Driver.objects.create(
            nombre='Busy Driver',
            activo=True,
            presente=True,
            num_entregas_dia=3,
            max_entregas_dia=3
        )
        self.assertFalse(driver.esta_disponible)
    
    def test_driver_not_available_when_inactive(self):
        """Test driver is not available when inactive"""
        driver = Driver.objects.create(
            nombre='Inactive Driver',
            activo=False,
            presente=True,
            num_entregas_dia=0,
            max_entregas_dia=3
        )
        self.assertFalse(driver.esta_disponible)
    
    def test_actualizar_posicion(self):
        """Test position update method"""
        driver = Driver.objects.create(nombre='Test Driver')
        
        driver.actualizar_posicion(-33.4569, -70.6483, 10.5)
        
        driver.refresh_from_db()
        self.assertEqual(float(driver.ultima_posicion_lat), -33.4569)
        self.assertEqual(float(driver.ultima_posicion_lng), -70.6483)
        self.assertIsNotNone(driver.ultima_actualizacion_posicion)
        
        # Verify history was created
        self.assertEqual(DriverLocation.objects.filter(driver=driver).count(), 1)
    
    def test_reset_entregas_diarias(self):
        """Test daily deliveries reset"""
        driver = Driver.objects.create(
            nombre='Test Driver',
            num_entregas_dia=5
        )
        
        driver.reset_entregas_diarias()
        
        driver.refresh_from_db()
        self.assertEqual(driver.num_entregas_dia, 0)