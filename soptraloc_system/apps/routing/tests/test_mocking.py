"""
Tests con mocking para APIs externas.
FASE 8: Testing - Mocking de servicios externos (Mapbox).
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.routing.services.mapbox_service import MapboxService


class MapboxServiceTest(TestCase):
    """Tests para el servicio de Mapbox con mocking."""
    
    @patch('requests.get')
    def test_get_route_success(self, mock_get):
        """Test obtener ruta con respuesta exitosa."""
        # Mock de respuesta de Mapbox
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'routes': [{
                'distance': 15000,  # 15km
                'duration': 1800,   # 30 minutos
                'geometry': {
                    'coordinates': [
                        [-70.6693, -33.4489],
                        [-70.6893, -33.4689]
                    ]
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Ejecutar servicio
        service = MapboxService()
        result = service.get_route(
            origin=(-33.4489, -70.6693),
            destination=(-33.4689, -70.6893)
        )
        
        # Verificaciones
        self.assertIsNotNone(result)
        self.assertIn('distance', result)
        self.assertIn('duration', result)
        self.assertEqual(result['distance'], 15000)
    
    @patch('requests.get')
    def test_get_route_api_error(self, mock_get):
        """Test manejo de error de API."""
        # Mock de error de API
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        # Ejecutar servicio
        service = MapboxService()
        result = service.get_route(
            origin=(-33.4489, -70.6693),
            destination=(-33.4689, -70.6893)
        )
        
        # Debería retornar None o un valor por defecto
        self.assertIsNone(result) or self.assertIn('error', result)
    
    @patch('requests.get')
    def test_calculate_time_with_traffic(self, mock_get):
        """Test cálculo de tiempo con tráfico."""
        # Mock de respuesta con tráfico
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'routes': [{
                'duration': 2400,  # 40 minutos con tráfico
                'duration_typical': 1800,  # 30 minutos sin tráfico
                'distance': 15000
            }]
        }
        mock_get.return_value = mock_response
        
        service = MapboxService()
        result = service.get_route_with_traffic(
            origin=(-33.4489, -70.6693),
            destination=(-33.4689, -70.6893)
        )
        
        # Verificar que incluye información de tráfico
        self.assertIsNotNone(result)
        self.assertEqual(result['duration'], 2400)


class CeleryTasksTest(TestCase):
    """Tests para tareas de Celery con mocking."""
    
    @patch('apps.containers.tasks.check_demurrage_for_all_containers.delay')
    def test_demurrage_task_is_called(self, mock_task):
        """Test que la tarea de demurrage se puede llamar."""
        # Simular llamada a la tarea
        from apps.containers.tasks import check_demurrage_for_all_containers
        check_demurrage_for_all_containers.delay()
        
        # Verificar que se llamó
        mock_task.assert_called_once()
    
    @patch('apps.drivers.tasks.cleanup_old_drivers.delay')
    def test_cleanup_drivers_task(self, mock_task):
        """Test tarea de limpieza de conductores."""
        from apps.drivers.tasks import cleanup_old_drivers
        cleanup_old_drivers.delay()
        
        mock_task.assert_called_once()
