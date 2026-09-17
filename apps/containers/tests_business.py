"""Tests de negocio del FSM + señales (vida real del contenedor, no mocks)."""
import uuid

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD
from apps.programaciones.models import Programacion
from apps.events.models import Event


class ContainerLifecycleTest(TestCase):
    """Camina el ciclo completo del contenedor contra modelos reales."""

    def setUp(self):
        self.suf = uuid.uuid4().hex[:6]
        self.cd = CD.objects.create(
            nombre=f'CD TEST {self.suf}', tipo='cliente', direccion='Av Test 1',
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

    def test_ciclo_completo_fsm(self):
        c = self.cont
        self.assertEqual(c.estado, 'por_arribar')

        c.cambiar_estado('liberado', 'test')
        c.refresh_from_db()
        self.assertEqual(c.estado, 'liberado')
        self.assertIsNotNone(c.fecha_liberacion)

        c.cambiar_estado('secuenciado', 'test')
        c.refresh_from_db()
        self.assertEqual(c.estado, 'secuenciado')
        self.assertIsNotNone(c.fecha_secuenciado)

        c.cambiar_estado('programado', 'test')
        c.refresh_from_db()
        self.assertEqual(c.estado, 'programado')
        # La señal crear_programacion_automatica debe haber creado la Programacion
        prog = Programacion.objects.filter(container=c).first()
        self.assertIsNotNone(prog, 'La señal no creó la programación al pasar a programado')

        # Asignación (si la automatización no lo hizo antes)
        if prog.driver is None:
            prog.asignar_conductor(self.drv, 'test')
        c.refresh_from_db(); prog.refresh_from_db(); self.drv.refresh_from_db()
        self.assertEqual(c.estado, 'asignado')
        self.assertIsNotNone(prog.driver)
        self.assertEqual(self.drv.num_entregas_dia, 1)
        self.assertTrue(Event.objects.filter(
            container=c, event_type='asignacion_conductor').exists())

        # Resto del ciclo
        for estado in ['en_ruta', 'entregado', 'descargado', 'vacio', 'vacio_en_ruta', 'devuelto']:
            c.cambiar_estado(estado, 'test')
            c.refresh_from_db()
            self.assertEqual(c.estado, estado)
        self.assertIsNotNone(c.fecha_devolucion)

    def test_guardia_rechaza_transicion_invalida(self):
        self.cont.cambiar_estado('liberado', 'test')
        self.cont.cambiar_estado('secuenciado', 'test')
        self.cont.cambiar_estado('programado', 'test')
        # programado -> en_ruta NO es transición válida (falta asignado)
        with self.assertRaises(ValidationError):
            self.cont.cambiar_estado('en_ruta', 'test')

    def test_guardia_rechaza_estado_terminal(self):
        # devuelto es terminal; saltar directo desde por_arribar debe lanzar
        with self.assertRaises(ValidationError):
            self.cont.cambiar_estado('devuelto', 'test')

    def test_señal_crea_programacion_solo_con_cd(self):
        # Sin cd_entrega la señal NO debe inventar una programación
        c = Container.objects.create(
            container_id=f'CCCC{uuid.uuid4().hex[:6]}', tipo='20DC',
            cliente='TEST', posicion_fisica='T1',
        )
        c.cambiar_estado('liberado', 'test')
        c.cambiar_estado('secuenciado', 'test')
        c.cambiar_estado('programado', 'test')
        self.assertIsNone(Programacion.objects.filter(container=c).first())

    def test_rollback_deja_bd_limpia(self):
        with transaction.atomic():
            Container.objects.create(
                container_id=f'BBBB{uuid.uuid4().hex[:6]}', tipo='20DC',
                cliente='TEST', posicion_fisica='T1',
            )
            transaction.set_rollback(True)
        self.assertIsNone(Container.objects.filter(container_id__startswith='BBBB').first())