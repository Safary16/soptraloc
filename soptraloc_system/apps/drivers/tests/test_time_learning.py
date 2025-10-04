from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.containers.models import Container
from apps.core.models import Company
from apps.drivers.models import Assignment, Driver, Location, TimeMatrix
from apps.drivers.services.duration_predictor import DriverDurationPredictor

try:  # pragma: no cover - las pruebas se ajustan si no hay scikit-learn disponible
    from sklearn.linear_model import SGDRegressor  # noqa: F401
    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover
    SKLEARN_AVAILABLE = False


class AssignmentLearningTestCase(TestCase):
    def setUp(self):
        self.origin = Location.objects.create(name='CCTI Base', code='CCTI', address='Maipú')
        self.destination = Location.objects.create(name='CD Quilicura', code='CD_QUILICURA', address='Quilicura')
        self.time_matrix = TimeMatrix.objects.create(
            from_location=self.origin,
            to_location=self.destination,
            travel_time=90,
            loading_time=15,
            unloading_time=20,
        )

        self.company = Company.objects.create(
            name='Demo Company',
            code='DEMO',
            rut='12345678-9',
            email='ops@demo.test',
            phone='+56912345678',
            address='Dirección demo'
        )

        self.driver = Driver.objects.create(
            nombre='Juan Pérez',
            rut='11111111-1',
            telefono='+56911111111',
            ppu='AA11',
            tracto='TRACTO1',
            tipo_conductor='TRONCO',
            estado='OPERATIVO',
            ubicacion_actual='CCTI'
        )

        self.container = Container.objects.create(
            container_number='DEM1234567',
            container_type='40ft',
            status='PROGRAMADO',
            owner_company=self.company,
            service_type='DIRECTO',
            current_position='CCTI'
        )

    def test_record_actual_times_updates_matrix(self):
        assignment = Assignment.objects.create(
            container=self.container,
            driver=self.driver,
            fecha_programada=timezone.now() - timedelta(hours=4),
            fecha_inicio=timezone.now() - timedelta(hours=3),
            estado='EN_CURSO',
            origen=self.origin,
            destino=self.destination,
            origen_legacy='CCTI',
            destino_legacy='CD Quilicura',
            tipo_asignacion='ENTREGA',
            tiempo_estimado=120,
        )

        assignment.record_actual_times(total_minutes=180, route_minutes=120, unloading_minutes=60)

        assignment.refresh_from_db()
        self.time_matrix.refresh_from_db()

        self.assertEqual(assignment.estado, 'COMPLETADA')
        self.assertEqual(assignment.tiempo_real, 180)
        self.assertEqual(assignment.ruta_minutos_real, 120)
        self.assertEqual(assignment.descarga_minutos_real, 60)
        self.assertGreaterEqual(self.time_matrix.total_trips, 1)
        self.assertAlmostEqual(self.time_matrix.avg_travel_time, 120, delta=1)
        self.assertEqual(self.time_matrix.travel_time, 120)
        self.assertGreaterEqual(self.time_matrix.unloading_time, 60)

    def test_predictor_uses_matrix_when_no_history(self):
        predictor = DriverDurationPredictor()
        prediction = predictor.predict(
            origin=self.origin,
            destination=self.destination,
            assignment_type='ENTREGA',
            scheduled_datetime=timezone.now(),
        )

        expected = self.time_matrix.get_total_time()
        self.assertEqual(prediction.minutes, expected)
        self.assertEqual(prediction.source, 'matrix')

    def test_predictor_learns_from_history(self):
        if not SKLEARN_AVAILABLE:
            self.skipTest('scikit-learn no disponible en el entorno de pruebas')

        base_start = timezone.now() - timedelta(days=5)
        durations = [150 + (idx % 5) * 10 for idx in range(25)]  # Distribución creciente

        Assignment.objects.all().delete()

        for idx, minutes in enumerate(durations):
            start = base_start + timedelta(hours=idx)
            Assignment.objects.create(
                container=self.container,
                driver=self.driver,
                fecha_programada=start,
                fecha_inicio=start,
                fecha_completada=start + timedelta(minutes=minutes),
                estado='COMPLETADA',
                origen=self.origin,
                destino=self.destination,
                origen_legacy='CCTI',
                destino_legacy='CD Quilicura',
                tipo_asignacion='ENTREGA',
                tiempo_estimado=120,
                tiempo_real=minutes,
                ruta_minutos_real=max(minutes - 30, 60),
                descarga_minutos_real=30,
            )

        predictor = DriverDurationPredictor()
        prediction = predictor.predict(
            origin=self.origin,
            destination=self.destination,
            assignment_type='ENTREGA',
            scheduled_datetime=timezone.now(),
        )

        historical_average = sum(durations) / len(durations)
        self.assertGreaterEqual(prediction.minutes, 0)
        self.assertAlmostEqual(prediction.minutes, historical_average, delta=35)
        self.assertIn(prediction.source, {'ml', 'historical'})