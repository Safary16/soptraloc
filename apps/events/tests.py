from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.containers.models import Container
from apps.events.models import Event


class EventModelTests(TestCase):
    """TAREA 1 (auditoría Flaco 2026-10-02): apps/events es la columna de
    auditoría del FSM — todo cambio de estado del ciclo de vida del contenedor
    emite un Event. Estos tests protegen creación, orden y representación."""

    def setUp(self):
        self.container = Container.objects.create(
            container_id='EVTU1234567', estado='liberado', cliente='Cliente'
        )

    def _event(self, event_type='cambio_estado', **kwargs):
        defaults = {
            'container': self.container,
            'event_type': event_type,
            'detalles': {'estado_anterior': 'liberado', 'estado_nuevo': 'secuenciado'},
            'usuario': 'test_user',
        }
        defaults.update(kwargs)
        return Event.objects.create(**defaults)

    def test_event_creation_with_all_core_types(self):
        """Los tipos núcleo del ciclo se crean y persisten correctamente."""
        core_types = [
            'cambio_estado', 'asignacion_driver', 'inicio_ruta',
            'arribo_cd', 'contenedor_vacio', 'devolucion_vacio',
            'incidente_reportado', 'alerta_48h',
        ]
        for event_type in core_types:
            event = self._event(event_type=event_type)
            self.assertEqual(event.event_type, event_type)
            self.assertEqual(event.container, self.container)
        self.assertEqual(Event.objects.count(), len(core_types))

    def test_str_includes_type_container_and_timestamp(self):
        event = self._event(event_type='inicio_ruta')
        text = str(event)
        self.assertIn('Inicio de Ruta', text)
        self.assertIn('EVTU1234567', text)

    def test_ordering_is_most_recent_first(self):
        old = self._event()
        new = self._event(detalles={'note': 'later'})
        # Force distinct timestamps: created_at usa auto_now_add, así que
        # actualizamos el viejo explícitamente hacia atrás.
        Event.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(hours=1))
        events = list(Event.objects.all())
        self.assertEqual(events[0], new)
        self.assertEqual(events[-1], old)

    def test_detalles_json_default_empty_dict(self):
        event = Event.objects.create(container=self.container, event_type='sin_conductor')
        self.assertEqual(event.detalles, {})

    def test_usuario_can_be_null(self):
        event = Event.objects.create(container=self.container, event_type='demurrage_cercano')
        self.assertIsNone(event.usuario)


class EventFSMAuditTrailTests(TestCase):
    """Contrato de integración: cada transición FSM del container debe emitir
    un Event('cambio_estado') con detalles y usuario — la base de la auditoría."""

    def setUp(self):
        self.container = Container.objects.create(
            container_id='FSMA1234567', estado='por_arribar', cliente='Cliente'
        )

    def test_cambiar_estado_emits_audit_event(self):
        self.container.cambiar_estado('liberado', usuario='operador_test')
        events = Event.objects.filter(container=self.container, event_type='cambio_estado')
        self.assertEqual(events.count(), 1)
        event = events.first()
        detalles = event.detalles
        self.assertEqual(detalles.get('estado_anterior'), 'por_arribar')
        self.assertEqual(detalles.get('estado_nuevo'), 'liberado')
        self.assertEqual(event.usuario, 'operador_test')

    def test_invalid_transition_raises_and_emits_nothing(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.container.cambiar_estado('en_ruta')  # por_arribar → en_ruta NO es válida
        self.assertEqual(
            Event.objects.filter(container=self.container, event_type='cambio_estado').count(), 0
        )

    def test_chained_transitions_leave_full_trail(self):
        self.container.cambiar_estado('liberado', usuario='op1')
        self.container.cambiar_estado('secuenciado', usuario='op2')
        self.container.cambiar_estado('programado', usuario='op3')
        trail = list(
            Event.objects.filter(
                container=self.container, event_type='cambio_estado'
            ).order_by('created_at')
        )
        self.assertEqual(len(trail), 3)
        self.assertEqual(trail[0].detalles.get('estado_nuevo'), 'liberado')
        self.assertEqual(trail[-1].detalles.get('estado_nuevo'), 'programado')
        self.assertEqual([e.usuario for e in trail], ['op1', 'op2', 'op3'])


class AuditoriaEventsAPITests(TestCase):
    """GET /api/auditoria/ — consulta del registro de eventos."""

    def setUp(self):
        self.client = APIClient()
        self.container = Container.objects.create(
            container_id='APIE1234567', estado='liberado', cliente='Cliente'
        )
        self.other = Container.objects.create(
            container_id='APIF7654321', estado='liberado', cliente='Cliente'
        )
        for index in range(5):
            Event.objects.create(
                container=self.container,
                event_type='cambio_estado',
                detalles={'i': index},
            )
        Event.objects.create(container=self.other, event_type='inicio_ruta')

    def test_endpoint_lists_events_with_select_related(self):
        response = self.client.get('/api/auditoria/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total'], 6)
        self.assertEqual(len(data['eventos']), 6)
        self.assertEqual(len(data['event_types']), len(Event.EVENT_TYPES))

    def test_filter_by_container_id_text(self):
        response = self.client.get('/api/auditoria/?container_id=APIE1234567')
        data = response.json()
        self.assertEqual(data['total'], 5)
        for evento in data['eventos']:
            self.assertEqual(evento['container_id'], 'APIE1234567')

    def test_filter_by_event_type(self):
        response = self.client.comb = self.client.get('/api/auditoria/?event_type=inicio_ruta')
        data = response.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['eventos'][0]['event_type'], 'inicio_ruta')

    def test_pagination_limit_offset(self):
        response = self.client.get('/api/auditoria/?limit=3&offset=0')
        data = response.json()
        self.assertEqual(len(data['eventos']), 3)
        self.assertEqual(data['limit'], 3)
        self.assertEqual(data['offset'], 0)
        response2 = self.client.get('/api/auditoria/?limit=3&offset=3')
        self.assertEqual(len(response2.json()['eventos']), 3)

    def test_limit_is_capped_at_500(self):
        response = self.client.get('/api/auditoria/?limit=9999')
        self.assertEqual(response.json()['limit'], 500)

    def test_non_numeric_limit_returns_400_not_500(self):
        """Bug detectado en auditoría Flaco 2026-10-02: limit/offset hacen
        int() sin try — '?limit=abc' lanzaba 500. Con el fix, responde 400."""
        response = self.client.get('/api/auditoria/?limit=abc')
        self.assertEqual(response.status_code, 400)

    def test_negative_offset_clamped_to_zero(self):
        response = self.client.get('/api/auditoria/?offset=-5')
        self.assertEqual(response.json()['offset'], 0)
