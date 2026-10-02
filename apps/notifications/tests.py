from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.notifications.models import Notification


_CONTAINER_SEQ = 0


def _make_notification(**kwargs):
    global _CONTAINER_SEQ
    _CONTAINER_SEQ += 1
    container = kwargs.pop('container', None) or Container.objects.create(
        container_id=f'NOTT{_CONTAINER_SEQ:08d}'[:11].ljust(11, 'X'),
        estado='liberado', cliente='Cliente',
    )
    defaults = {
        'container': container,
        'tipo': 'ruta_iniciada',
        'prioridad': 'media',
        'titulo': 'Notificación de prueba',
        'mensaje': 'Mensaje de prueba',
    }
    defaults.update(kwargs)
    return Notification.objects.create(**defaults)


class NotificationModelTests(TestCase):
    """TAREA 1 (auditoría Flaco 2026-10-02): ciclo de estado de Notification."""

    def setUp(self):
        self.container = Container.objects.create(
            container_id='NOTM1234567', estado='liberado', cliente='Cliente'
        )

    def _notification(self, **kwargs):
        defaults = {
            'container': self.container,
            'tipo': 'arribo_proximo',
            'titulo': 'Arribo próximo',
            'mensaje': 'El contenedor está cerca del CD',
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    def test_default_state_is_pendiente_with_media_priority(self):
        notification = self._notification()
        self.assertEqual(notification.estado, 'pendiente')
        self.assertEqual(notification.prioridad, 'media')
        self.assertIsNone(notification.leida_at)

    def test_marcar_leida_sets_state_and_timestamp(self):
        notification = self._notification()
        notification.marcar_leida()
        notification.refresh_from_db()
        self.assertEqual(notification.estado, 'leida')
        self.assertIsNotNone(notification.leida_at)

    def test_marcar_leida_is_idempotent_for_leida(self):
        notification = self._notification()
        notification.marcar_leida()
        first_leida_at = notification.leida_at
        notification.marcar_leida()
        notification.refresh_from_db()
        # Ya está leída: el segundo llamado no debe tocar el timestamp.
        self.assertEqual(notification.leida_at, first_leida_at)

    def test_marcar_leida_ignored_when_archivada(self):
        notification = self._notification(estado='archivada')
        notification.marcar_leida()
        notification.refresh_from_db()
        self.assertEqual(notification.estado, 'archivada')

    def test_archivar_sets_state(self):
        notification = self._notification(estado='enviada')
        notification.archivar()
        notification.refresh_from_db()
        self.assertEqual(notification.estado, 'archivada')

    def test_notification_with_driver_and_programacion_optional(self):
        driver = Driver.objects.create(nombre='Driver Notif')
        notification = self._notification(driver=driver)
        self.assertEqual(notification.driver, driver)
        self.assertIsNone(notification.programacion)


class NotificationViewSetTests(TestCase):
    """Acciones del ViewSet: activas, recientes, mark-read, archivar, limpiar."""

    def setUp(self):
        self.client = APIClient()
        # Los POST del ViewSet requieren autenticación (IsAuthenticatedOrReadOnly):
        # comportamiento correcto, no se toca. Los tests autentican un usuario.
        self.user = User.objects.create_user(username='notif_tester', password='pass123')
        self.client.force_authenticate(user=self.user)
        self.container = Container.objects.create(
            container_id='NOTV1234567', estado='liberado', cliente='Cliente'
        )
        self.pendiente = Notification.objects.create(
            container=self.container, tipo='ruta_iniciada',
            titulo='P1', mensaje='m', estado='pendiente',
        )
        self.enviada = Notification.objects.create(
            container=self.container, tipo='eta_actualizado',
            titulo='P2', mensaje='m', estado='enviada',
        )
        self.leida = Notification.objects.create(
            container=self.container, tipo='llegada',
            titulo='P3', mensaje='m', estado='leida',
        )

    def test_activas_only_pendiente_y_enviada(self):
        response = self.client.get('/api/notifications/activas/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        ids = {n['id'] for n in data['notificaciones']}
        self.assertIn(self.pendiente.id, ids)
        self.assertIn(self.enviada.id, ids)
        self.assertNotIn(self.leida.id, ids)

    def test_recientes_only_last_30_minutes(self):
        vieja = Notification.objects.create(
            container=self.container, tipo='ruta_iniciada',
            titulo='Vieja', mensaje='m', estado='pendiente',
        )
        Notification.objects.filter(pk=vieja.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        response = self.client.get('/api/notifications/recientes/')
        data = response.json()
        ids = {n['id'] for n in data['notificaciones']}
        self.assertNotIn(vieja.id, ids)
        self.assertIn(self.pendiente.id, ids)

    def test_marcar_leida_action(self):
        response = self.client.post(f'/api/notifications/{self.pendiente.id}/marcar_leida/')
        self.assertEqual(response.status_code, 200)
        self.pendiente.refresh_from_db()
        self.assertEqual(self.pendiente.estado, 'leida')
        self.assertIsNotNone(self.pendiente.leida_at)

    def test_archivar_action(self):
        response = self.client.post(f'/api/notifications/{self.enviada.id}/archivar/')
        self.assertEqual(response.status_code, 200)
        self.enviada.refresh_from_db()
        self.assertEqual(self.enviada.estado, 'archivada')

    def test_marcar_todas_leidas_counts_only_active(self):
        response = self.client.post('/api/notifications/marcar_todas_leidas/')
        data = response.json()
        # pendiente + enviada = 2; la leída no cuenta.
        self.assertEqual(data['total'], 2)
        self.leida.refresh_from_db()
        self.pendiente.refresh_from_db()
        self.assertEqual(self.pendiente.estado, 'leida')
        self.assertEqual(self.leida.estado, 'leida')

    def test_limpiar_antiguas_archives_old_enviada_leida_only(self):
        """limpiar_notificaciones_antiguas archiva SOLO enviada/leida (service
        línea 353): las pendiente se preservan por diseño — no se pierden
        alertas sin enviar. Verificado en auditoría Flaco 2026-10-02."""
        vieja_enviada = Notification.objects.create(
            container=self.container, tipo='ruta_iniciada',
            titulo='Vieja enviada', mensaje='m', estado='enviada',
        )
        vieja_pendiente = Notification.objects.create(
            container=self.container, tipo='ruta_iniciada',
            titulo='Vieja pendiente', mensaje='m', estado='pendiente',
        )
        Notification.objects.filter(pk__in=[vieja_enviada.pk, vieja_pendiente.pk]).update(
            created_at=timezone.now() - timedelta(days=30)
        )
        response = self.client.post(
            '/api/notifications/limpiar_antiguas/', {'dias': 7}, format='json'
        )
        data = response.json()
        self.assertEqual(data['total'], 1)
        vieja_enviada.refresh_from_db()
        self.assertEqual(vieja_enviada.estado, 'archivada')
        # La pendiente antigua NO se toca (comportamiento del service).
        vieja_pendiente.refresh_from_db()
        self.assertEqual(vieja_pendiente.estado, 'pendiente')
        # La reciente pendiente tampoco.
        self.pendiente.refresh_from_db()
        self.assertEqual(self.pendiente.estado, 'pendiente')

    def test_list_uses_reduced_serializer(self):
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertTrue(results)
        self.assertIn('titulo', results[0])
