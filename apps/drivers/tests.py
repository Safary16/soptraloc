from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Driver, DriverLocation
from decimal import Decimal


class DriverAuthenticationTestCase(TestCase):
    """Tests for driver user authentication"""
    
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='test_driver',
            password='testpass123',
            first_name='Test',
            last_name='Driver'
        )
        
        # Create a driver
        self.driver = Driver.objects.create(
            user=self.user,
            nombre='Test Driver',
            rut='12345678-9',
            telefono='+56912345678',
            presente=True,
            activo=True
        )
        
        self.client = Client()
    
    def test_driver_login_page(self):
        """Test driver login page is accessible"""
        response = self.client.get(reverse('driver_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard del Conductor')
    
    def test_driver_login_success(self):
        """Test successful driver login"""
        response = self.client.post(reverse('driver_login'), {
            'username': 'test_driver',
            'password': 'testpass123'
        })
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('driver_dashboard'))
    
    def test_driver_login_failure(self):
        """Test failed driver login"""
        response = self.client.post(reverse('driver_login'), {
            'username': 'test_driver',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')
    
    def test_driver_dashboard_requires_authentication(self):
        """Test that driver dashboard requires login"""
        response = self.client.get(reverse('driver_dashboard'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/driver/login/', response.url)
    
    def test_driver_dashboard_accessible_when_authenticated(self):
        """Test driver dashboard is accessible when logged in"""
        self.client.login(username='test_driver', password='testpass123')
        response = self.client.get(reverse('driver_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Driver')
    
    def test_driver_logout(self):
        """Test driver logout"""
        self.client.login(username='test_driver', password='testpass123')
        response = self.client.get(reverse('driver_logout'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('driver_login'))


class DriverGPSTrackingTestCase(TestCase):
    """Tests for GPS tracking functionality"""
    
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='gps_driver',
            password='testpass123'
        )
        
        # Create a driver
        self.driver = Driver.objects.create(
            user=self.user,
            nombre='GPS Test Driver',
            presente=True,
            activo=True
        )
        
        self.client = Client()
        self.client.login(username='gps_driver', password='testpass123')
    
    def test_track_location_api(self):
        """Test tracking location via API"""
        response = self.client.post(
            reverse('driver-track-location', kwargs={'pk': self.driver.id}),
            {
                'lat': -33.4489,
                'lng': -70.6693,
                'accuracy': 10.5
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Check that location was saved
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.ultima_posicion_lat, Decimal('-33.448900'))
        self.assertEqual(self.driver.ultima_posicion_lng, Decimal('-70.669300'))
        
        # Check that location history was created
        self.assertEqual(DriverLocation.objects.filter(driver=self.driver).count(), 1)
    
    def test_track_location_requires_authentication(self):
        """Test that tracking requires authentication"""
        self.client.logout()
        response = self.client.post(
            reverse('driver-track-location', kwargs={'pk': self.driver.id}),
            {'lat': -33.4489, 'lng': -70.6693},
            content_type='application/json'
        )
        # 401 = not authenticated (correct)
        self.assertIn(response.status_code, [401, 403])
    
    def test_track_location_wrong_driver(self):
        """Test that driver can only track own location"""
        # Create another driver
        other_user = User.objects.create_user(username='other_driver', password='pass')
        other_driver = Driver.objects.create(
            user=other_user,
            nombre='Other Driver'
        )
        
        # Try to track other driver's location
        response = self.client.post(
            reverse('driver-track-location', kwargs={'pk': other_driver.id}),
            {'lat': -33.4489, 'lng': -70.6693},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
    
    def test_active_locations_api(self):
        """Test active locations API"""
        # Set a recent position for the driver
        self.driver.actualizar_posicion(-33.4489, -70.6693)
        
        response = self.client.get(reverse('driver-active-locations'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['drivers'][0]['nombre'], 'GPS Test Driver')


class DriverModelTestCase(TestCase):
    """Tests for Driver model"""
    
    def test_driver_creation_with_user(self):
        """Test creating a driver with a user"""
        user = User.objects.create_user(username='model_test', password='pass')
        driver = Driver.objects.create(
            user=user,
            nombre='Model Test Driver',
            rut='11111111-1'
        )
        self.assertEqual(driver.user, user)
        self.assertEqual(user.driver_profile, driver)
    
    def test_driver_location_history(self):
        """Test driver location history"""
        driver = Driver.objects.create(nombre='Location Test')
        
        # Create multiple location entries
        DriverLocation.objects.create(
            driver=driver,
            lat=Decimal('-33.4489'),
            lng=Decimal('-70.6693'),
            accuracy=10.0
        )
        DriverLocation.objects.create(
            driver=driver,
            lat=Decimal('-33.4500'),
            lng=Decimal('-70.6700'),
            accuracy=15.0
        )
        
        # Check history
        self.assertEqual(driver.location_history.count(), 2)
        
        # Check ordering (most recent first)
        locations = list(driver.location_history.all())
        self.assertGreater(locations[0].timestamp, locations[1].timestamp)
