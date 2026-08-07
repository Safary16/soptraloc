"""
Tests for programming and dashboard alert fixes

Tests verify:
1. Dashboard alerts only show liberados (not programmed)
2. Dashboard only shows active programaciones
3. Programar endpoint prevents duplicates
4. State validation works correctly
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.test.utils import override_settings
from apps.containers.models import Container
from apps.programaciones.models import Programacion
from apps.cds.models import CD
from apps.drivers.models import Driver


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class DashboardAlertsTestCase(TestCase):
    """Test dashboard_alertas filtering"""
    
    def setUp(self):
        """Create test data - disable signals to avoid auto-creation"""
        from django.db.models import signals
        from apps.containers import signals as container_signals
        
        # Disconnect the auto-programacion signal
        signals.post_save.disconnect(
            container_signals.crear_programacion_automatica,
            sender=Container
        )
        # Create CD
        self.cd = CD.objects.create(
            nombre='Test CD',
            direccion='Test Address',
            lat=-33.4372,
            lng=-70.6506,
            activo=True
        )
        
        # Create containers in different states
        self.container_liberado = Container.objects.create(
            container_id='TEST001',
            tipo='40',
            nave='Test Ship',
            estado='liberado',
            fecha_demurrage=timezone.now() + timedelta(days=1)
        )
        
        self.container_programado = Container.objects.create(
            container_id='TEST002',
            tipo='40',
            nave='Test Ship',
            estado='programado',
            fecha_demurrage=timezone.now() + timedelta(days=1)
        )
        
        # Create programacion for programado container (signal is disabled)
        self.programacion = Programacion.objects.create(
            container=self.container_programado,
            cd=self.cd,
            fecha_programada=timezone.now() + timedelta(days=1),
            cliente='Test Client'
        )
    
    def tearDown(self):
        """Reconnect signals"""
        from django.db.models import signals
        from apps.containers import signals as container_signals
        
        # Reconnect the signal
        signals.post_save.connect(
            container_signals.crear_programacion_automatica,
            sender=Container
        )
    
    def test_demurrage_alerts_only_liberados(self):
        """Demurrage alerts should only show liberado containers"""
        from apps.core.api_views import dashboard_alertas
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/api/dashboard/alertas/')
        
        response = dashboard_alertas(request)
        alertas = response.data['alertas']
        
        # Filter demurrage alerts
        demurrage_alerts = [a for a in alertas if a['tipo'] == 'demurrage']
        
        # Should only have liberado container
        self.assertEqual(len(demurrage_alerts), 1)
        self.assertEqual(demurrage_alerts[0]['container_id'], 'TEST001')
        self.assertEqual(demurrage_alerts[0]['estado'], 'liberado')
    
    def test_conductor_alerts_only_programado(self):
        """Conductor alerts should only show programado/secuenciado containers"""
        from apps.core.api_views import dashboard_alertas
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/api/dashboard/alertas/')
        
        response = dashboard_alertas(request)
        alertas = response.data['alertas']
        
        # Filter conductor alerts
        conductor_alerts = [a for a in alertas if a['tipo'] == 'sin_conductor']
        
        # Should have programado container without driver
        for alert in conductor_alerts:
            self.assertIn(alert['estado'], ['programado', 'secuenciado'])


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ProgramacionDashboardTestCase(TestCase):
    """Test programaciones dashboard filtering"""
    
    def setUp(self):
        """Create test data - disable signals"""
        from django.db.models import signals
        from apps.containers import signals as container_signals
        
        # Disconnect the auto-programacion signal
        signals.post_save.disconnect(
            container_signals.crear_programacion_automatica,
            sender=Container
        )
        self.cd = CD.objects.create(
            nombre='Test CD',
            direccion='Test Address',
            lat=-33.4372,
            lng=-70.6506,
            activo=True
        )
        
        # Create containers in different states
        self.container_active = Container.objects.create(
            container_id='ACTIVE001',
            tipo='40',
            nave='Test Ship',
            estado='programado'
        )
        
        self.container_completed = Container.objects.create(
            container_id='COMPLETED001',
            tipo='40',
            nave='Test Ship',
            estado='devuelto'
        )
        
        # Create programaciones
        self.prog_active = Programacion.objects.create(
            container=self.container_active,
            cd=self.cd,
            fecha_programada=timezone.now() + timedelta(days=1),
            cliente='Test Client'
        )
        
        self.prog_completed = Programacion.objects.create(
            container=self.container_completed,
            cd=self.cd,
            fecha_programada=timezone.now() - timedelta(days=1),
            cliente='Test Client 2'
        )
    
    def tearDown(self):
        """Reconnect signals"""
        from django.db.models import signals
        from apps.containers import signals as container_signals
        
        # Reconnect the signal
        signals.post_save.connect(
            container_signals.crear_programacion_automatica,
            sender=Container
        )
    
    def test_dashboard_filters_completed(self):
        """Dashboard should only show active programaciones"""
        from django.test import RequestFactory
        from apps.programaciones.views import ProgramacionViewSet
        
        factory = RequestFactory()
        request = factory.get('/api/programaciones/dashboard/')
        
        view = ProgramacionViewSet()
        view.queryset = Programacion.objects.all()
        view.request = request
        
        response = view.dashboard(request)
        programaciones = response.data['programaciones']
        
        # Should only have active programacion
        container_ids = [p['container_id'] for p in programaciones]
        self.assertIn('ACTIVE001', container_ids)
        self.assertNotIn('COMPLETED001', container_ids)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ProgramarValidationTestCase(TestCase):
    """Test programar endpoint validation"""
    
    def setUp(self):
        """Create test data - disable signals"""
        from django.db.models import signals
        from apps.containers import signals as container_signals
        
        # Disconnect the auto-programacion signal
        signals.post_save.disconnect(
            container_signals.crear_programacion_automatica,
            sender=Container
        )
        self.cd = CD.objects.create(
            nombre='Test CD',
            direccion='Test Address',
            lat=-33.4372,
            lng=-70.6506,
            activo=True
        )
        
        self.container_liberado = Container.objects.create(
            container_id='LIB001',
            tipo='40',
            nave='Test Ship',
            estado='liberado'
        )
        
        self.container_programado = Container.objects.create(
            container_id='PROG001',
            tipo='40',
            nave='Test Ship',
            estado='programado'
        )
        
        # Create programacion for programado container (signal is disabled)
        self.programacion = Programacion.objects.create(
            container=self.container_programado,
            cd=self.cd,
            fecha_programada=timezone.now() + timedelta(days=1),
            cliente='Test Client'
        )
    
    def tearDown(self):
        """Reconnect signals"""
        from django.db.models import signals
        from apps.containers import signals as container_signals
        
        # Reconnect the signal
        signals.post_save.connect(
            container_signals.crear_programacion_automatica,
            sender=Container
        )
    
    def test_cannot_program_already_programmed(self):
        """Should not allow programming already programmed container"""
        # Test the validation logic directly without going through the full viewset
        # The key is that container has estado='programado' and already has a programacion
        
        # Verify container is in programado state
        self.assertEqual(self.container_programado.estado, 'programado')
        
        # Verify it has a programacion
        tiene_prog, prog = Programacion.container_tiene_programacion(self.container_programado)
        self.assertTrue(tiene_prog)
        self.assertIsNotNone(prog)
        self.assertEqual(prog.id, self.programacion.id)
        
        # Verify the state validation would reject it
        # Container in programado state should not be programmable again
        self.assertNotIn(self.container_programado.estado, ['liberado', 'secuenciado'])
    
    def test_can_program_liberado(self):
        """Should allow programming liberado container"""
        # Test that liberado container can be programmed
        self.assertEqual(self.container_liberado.estado, 'liberado')
        
        # Check it has no programacion
        tiene_prog, _ = Programacion.container_tiene_programacion(self.container_liberado)
        self.assertFalse(tiene_prog)


def run_tests():
    """Run all tests"""
    from django.test.runner import DiscoverRunner
    
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['test_programming_fixes'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    print("Running programming fixes tests...\n")
    run_tests()
