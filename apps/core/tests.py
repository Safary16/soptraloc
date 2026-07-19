from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.cds.models import CD
from apps.containers.models import Container
from apps.core.services.learning_engine import OperationalLearningEngine
from apps.drivers.models import Driver
from apps.programaciones.models import Programacion, TiempoViaje


class OperationalLearningEngineTests(TestCase):
    def setUp(self):
        self.driver = Driver.objects.create(nombre='ML Driver')
        self.cd = CD.objects.create(
            nombre='ML CD', codigo='ML-CD', direccion='Destino', comuna='Santiago',
            lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='MLAA1234567', estado='liberado', cliente='Cliente'
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, cliente='Cliente',
            fecha_programada=timezone.now() + timedelta(hours=2),
        )
        self.origin = (-33.50, -70.70)
        self.destination = (-33.45, -70.65)
        self.departure = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)

    def _trip(self, real, mapbox=40, driver=None, hour=8, signature='route-a', days_ago=1):
        departure = self.departure.replace(hour=hour) - timedelta(days=days_ago)
        return TiempoViaje.objects.create(
            conductor=driver or self.driver,
            programacion=None,
            origen_lat=self.origin[0], origen_lon=self.origin[1],
            destino_lat=self.destination[0], destino_lon=self.destination[1],
            origen_nombre='Origen', destino_nombre='Destino',
            tiempo_mapbox_min=mapbox, tiempo_real_min=real,
            hora_salida=departure, hora_llegada=departure + timedelta(minutes=real),
            hora_del_dia=hour, dia_semana=departure.weekday(),
            distancia_km=25, ruta_firma=signature, anomalia=False,
        )

    def test_cold_start_uses_mapbox_without_inventing_learning(self):
        route = {
            'duration_minutes': 40, 'distance_km': 25,
            'geometry': {'type': 'LineString', 'coordinates': []},
            'route_signature': 'route-a', 'route_index': 0,
        }
        prediction = OperationalLearningEngine.predict_route(
            self.origin, self.destination, self.departure, route, driver=self.driver
        )
        self.assertEqual(prediction['predicted_minutes'], 40)
        self.assertEqual(prediction['source'], 'mapbox_cold_start')
        self.assertEqual(prediction['samples'], 0)

    def test_history_adjusts_prediction_and_profiles_driver(self):
        for index, real in enumerate((52, 48, 50, 54, 46), start=1):
            self._trip(real=real, days_ago=index)
        route = {
            'duration_minutes': 40, 'distance_km': 25,
            'geometry': {'type': 'LineString', 'coordinates': [[0, 0], [1, 1]]},
            'route_signature': 'route-a', 'route_index': 0,
        }
        prediction = OperationalLearningEngine.predict_route(
            self.origin, self.destination, self.departure, route, driver=self.driver
        )
        profile = OperationalLearningEngine.driver_profile(self.driver)
        self.assertGreater(prediction['predicted_minutes'], 40)
        self.assertEqual(prediction['source'], 'hybrid_ml_mapbox')
        self.assertEqual(profile['label'], 'más_lento_que_referencia')
        self.assertGreaterEqual(profile['samples'], 5)

    @patch('apps.core.services.learning_engine.MapboxService.calcular_rutas_alternativas')
    def test_recommendation_compares_routes_and_hours(self, alternatives):
        alternatives.return_value = {
            'success': True,
            'routes': [
                {'route_index': 0, 'duration_minutes': 45, 'distance_km': 20,
                 'geometry': {'type': 'LineString', 'coordinates': [[0, 0]]}, 'route_signature': 'route-a'},
                {'route_index': 1, 'duration_minutes': 35, 'distance_km': 24,
                 'geometry': {'type': 'LineString', 'coordinates': [[1, 1]]}, 'route_signature': 'route-b'},
            ],
        }
        result = OperationalLearningEngine.recommend(
            self.origin, self.destination, self.departure, driver=self.driver, window_hours=2
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['recommended']['route_index'], 1)
        self.assertEqual(len(result['alternatives']), 5)
        self.assertTrue(result['cold_start'])

    def test_anomalous_trip_is_excluded(self):
        trip = self._trip(real=200)
        trip.anomalia = True
        trip.save(update_fields=['anomalia'])
        history = OperationalLearningEngine._history(self.origin, self.destination)
        self.assertEqual(history, [])
