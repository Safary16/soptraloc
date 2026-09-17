"""Tests de notificaciones: servicio central + ciclo de vida del modelo (real)."""
import uuid

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD
from apps.programaciones.models import Programacion
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


class NotificationBusinessTest(TestCase):
    """Cubre NotificationService y los métodos vivos de Notification (real, no mocks)."""

    def setUp(self):
        self.suf = uuid.uuid4().hex[:6]
        self.cd = CD.objects.create(
            nombre=f'CD {self.suf}', tipo='cliente', direccion='Av Test',
            lat=-33.45, lng=-70.66,
        )
        self.drv = Driver.objects.create(
            nombre=f'Pepe {self.suf}', rut=f'{self.suf}-{self.suf[:1]}',
            patente=f'AA{self.suf[:3]}', max_entregas_dia=5, activo=True, presente=True,
        )
        self.cont = Container.objects.create(
            container_id=f'AAAA{self.suf}', tipo='40HC', cliente='WALMART',
            posicion_fisica='P1', cd_entrega=self.cd,
        )
        self.prog = Programacion.objects.create(
            container=self.cont, cd=self.cd, fecha_programada=timezone.now() + timedelta(hours=4),
            cliente='WALMART', direccion_entrega='Av Test',
        )

    def test_crear_notificacion_asignacion(self):
        n = NotificationService.crear_notificacion_asignacion(self.prog, self.drv)
        self.assertIsNotNone(n.id)
        self.assertEqual(n.tipo, 'asignacion')
        self.assertEqual(n.container, self.cont)
        self.assertEqual(n.driver, self.drv)
        self.assertEqual(n.programacion, self.prog)
        self.assertIn(self.cont.container_id, n.titulo)

    def test_ciclo_vida_modelo_marcar_leida(self):
        n = NotificationService.crear_notificacion_asignacion(self.prog, self.drv)
        self.assertEqual(n.estado, 'pendiente')
        n.marcar_leida()
        n.refresh_from_db()
        self.assertEqual(n.estado, 'leida')
        self.assertIsNotNone(n.leida_at)

    def test_modelo_archivar(self):
        n = NotificationService.crear_notificacion_asignacion(self.prog, self.drv)
        n.archivar()
        n.refresh_from_db()
        self.assertEqual(n.estado, 'archivada')

    def test_obtener_notificaciones_activas_excluye_archivadas(self):
        n1 = NotificationService.crear_notificacion_asignacion(self.prog, self.drv)
        n1.archivar()
        activas = NotificationService.obtener_notificaciones_activas()
        self.assertNotIn(n1.id, [n.id for n in activas])

    def test_tiempo_desde_creacion_y_reciente(self):
        n = NotificationService.crear_notificacion_asignacion(self.prog, self.drv)
        self.assertTrue(n.es_reciente)          # creada ahora → reciente
        self.assertGreaterEqual(n.tiempo_desde_creacion, 0)

    def test_limpiar_notificaciones_antiguas(self):
        n = NotificationService.crear_notificacion_asignacion(self.prog, self.drv)
        # el servicio solo archiva estados enviada/leida con antigüedad > límite
        n.marcar_leida()
        Notification.objects.filter(pk=n.pk).update(created_at=timezone.now() - timedelta(days=30))
        archivadas = NotificationService.limpiar_notificaciones_antiguas(dias=7)
        self.assertEqual(archivadas, 1)
        n.refresh_from_db()
        self.assertEqual(n.estado, 'archivada')