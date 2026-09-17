"""Tests del flujo transaccional de retiro/retorno de vacíos (lógica real, no mocks)."""
import uuid

from django.test import TestCase

from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD
from apps.core.services.returns import EmptyReturnService
from apps.programaciones.models import Programacion


class EmptyReturnFlowTest(TestCase):
    """Cubre EmptyReturnService.start/complete: depósito y CCTI, con guardas reales."""

    def setUp(self):
        self.suf = uuid.uuid4().hex[:6]
        self.cd_origen = CD.objects.create(
            nombre=f'CD ORIGEN {self.suf}', tipo='cliente', direccion='Av Test 1',
            lat=-33.45, lng=-70.66, capacidad_vacios=10, vacios_actuales=2,
        )
        self.ccti = CD.objects.create(
            nombre=f'CCTI {self.suf}', tipo='ccti', direccion='Terminal 2',
            lat=-33.40, lng=-70.65, activo=True, capacidad_vacios=5, vacios_actuales=0,
        )
        self.drv = Driver.objects.create(
            nombre=f'Pepe {self.suf}', rut=f'{self.suf}-{self.suf[:1]}',
            patente=f'AA{self.suf[:3]}', max_entregas_dia=5, activo=True, presente=True,
        )
        self.cont = Container.objects.create(
            container_id=f'AAAA{self.suf}', tipo='40HC', cliente='WALMART',
            posicion_fisica='P1', cd_entrega=self.cd_origen, vacio_contabilizado=True,
        )

    def _llevar_a_vacio(self):
        """Camina el FSM hasta 'vacio' (precondición real del servicio)."""
        c = self.cont
        c.cambiar_estado('liberado', 'test')
        c.cambiar_estado('secuenciado', 'test')
        c.cambiar_estado('programado', 'test')
        prog = Programacion.objects.filter(container=c).first()
        if prog and prog.driver is None:
            prog.asignar_conductor(self.drv, 'test')
        c.refresh_from_db()  # asignar_conductor cambia estado en BD; refrescar antes de continuar
        self.assertEqual(c.estado, 'asignado')
        for estado in ['en_ruta', 'entregado', 'descargado', 'vacio']:
            c.cambiar_estado(estado, 'test')
            c.refresh_from_db()
        return c

    def test_retorno_a_deposito_completo(self):
        c = self._llevar_a_vacio()
        c = EmptyReturnService.start(c, destination_type='deposito', depot_name='DEPO TEST')
        c.refresh_from_db()
        self.assertEqual(c.estado, 'vacio_en_ruta')
        self.assertEqual(c.retorno_destino_tipo, 'deposito')
        self.assertEqual(c.deposito_devolucion, 'DEPO TEST')

        c = EmptyReturnService.complete(c, user='test')
        c.refresh_from_db()
        self.assertEqual(c.estado, 'devuelto')
        self.assertIsNotNone(c.fecha_devolucion)

    def test_retorno_a_ccti_recibe_vacio(self):
        c = self._llevar_a_vacio()
        c = EmptyReturnService.start(c, destination_type='ccti', destination_cd=self.ccti)
        c.refresh_from_db()
        self.assertEqual(c.estado, 'vacio_en_ruta')
        self.assertEqual(c.retorno_destino_tipo, 'ccti')
        self.assertEqual(c.retorno_destino_cd, self.ccti)

        c = EmptyReturnService.complete(c, user='test')
        c.refresh_from_db()
        self.assertEqual(c.estado, 'en_ccti')  # llega al CCTI
        self.assertEqual(c.cd_entrega, self.ccti)  # inventario se reasigna
        self.ccti.refresh_from_db()
        self.assertEqual(self.ccti.vacios_actuales, 1)  # CCTI recibió el vacío

    def test_start_rechaza_contenedor_no_vacio(self):
        # Un contenedor en 'liberado' NO puede iniciar retorno
        self.cont.cambiar_estado('liberado', 'test')
        with self.assertRaises(ValueError):
            EmptyReturnService.start(self.cont, destination_type='deposito', depot_name='DEPO')

    def test_start_rechaza_destino_invalido(self):
        c = self._llevar_a_vacio()
        with self.assertRaises(ValueError):
            EmptyReturnService.start(c, destination_type='luna')

    def test_start_requiere_depot_name_si_no_hay_deposito(self):
        c = self._llevar_a_vacio()
        with self.assertRaises(ValueError):
            EmptyReturnService.start(c, destination_type='deposito')  # sin depot_name

    def test_complete_sin_destino_configurado_lanza(self):
        c = self._llevar_a_vacio()
        c.cambiar_estado('vacio_en_ruta', 'test')  # forzar retorno sin destino seteado
        with self.assertRaises(ValueError):
            EmptyReturnService.complete(c, user='test')