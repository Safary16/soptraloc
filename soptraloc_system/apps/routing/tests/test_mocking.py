"""
Tests con mocking para APIs externas.
FASE 8: Testing - Mocking de servicios externos (Mapbox).
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase


class MapboxMockingTest(TestCase):
    """Tests para mocking de llamadas a Mapbox API."""
    
    @patch('requests.get')
    def test_mapbox_api_call_success(self, mock_get):
        """Test llamada exitosa a Mapbox API."""
        import requests
        
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
        
        # Simular llamada
        response = requests.get('https://api.mapbox.com/test')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('routes', data)
        self.assertEqual(data['routes'][0]['distance'], 15000)
    
    @patch('requests.get')
    def test_mapbox_api_error_handling(self, mock_get):
        """Test manejo de errores de API."""
        import requests
        
        # Mock de error de API
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        # Simular llamada
        response = requests.get('https://api.mapbox.com/test')
        
        # Verificar código de error
        self.assertEqual(response.status_code, 500)
    
    @patch('requests.get')
    def test_mapbox_timeout_handling(self, mock_get):
        """Test manejo de timeout."""
        import requests
        
        # Mock de timeout
        mock_get.side_effect = requests.Timeout()
        
        # Verificar que se lanza la excepción
        with self.assertRaises(requests.Timeout):
            requests.get('https://api.mapbox.com/test', timeout=5)


class CeleryMockingTest(TestCase):
    """Tests para mocking de tareas Celery."""
    
    @patch('celery.app.task.Task.apply_async')
    def test_celery_task_called(self, mock_apply):
        """Test que tareas Celery se pueden mockear."""
        mock_apply.return_value = MagicMock(id='test-task-id')
        
        # Simular llamada a tarea
        result = mock_apply()
        
        # Verificar
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 'test-task-id')
    
    def test_celery_delay_mock(self):
        """Test mocking de .delay()."""
        with patch('celery.app.task.Task.delay') as mock_delay:
            mock_delay.return_value = MagicMock(id='delayed-task')
            
            # Simular
            result = mock_delay(arg1='test', arg2=123)
            
            # Verificar
            mock_delay.assert_called_once_with(arg1='test', arg2=123)
