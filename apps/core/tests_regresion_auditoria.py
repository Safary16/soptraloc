"""
Tests de regresión de la auditoría 2026-09-18.

Cubren los hallazgos que la auditoría confirmó por simulación:
1. Retorno a CCTI: el vacío queda en 'en_ccti' (lugar físico) sin forzar 'devuelto'.
2. Desasignación: libera la capacidad del conductor (num_entregas_dia vuelve a 0).
3. Reversión del FSM: solo las transiciones en REVERSIONES_VALIDAS pueden revertir
   (nada de resucitar un 'devuelto' ni saltar el FSM arbitrariamente).
4. Vendor vacío ya no es P0 (no bloquea el despacho automático).
Nota: estos tests NO se leyeron de la suite existente; se escribieron desde la lógica del repo.
"""
import uuid

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.cds.models import CD
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.programaciones.models import Programacion
from apps.core.services.returns import EmptyReturnService


def _sufijo():
    return uuid.uuid4().hex[:6]


def _cd_cliente(suf):
    return CD.objects.create(
        nombre=f"CD_{suf}", codigo=f"C{suf}", direccion="Av 1", comuna="Santiago",
        tipo='cliente', lat=-33.45, lng=-70.66, capacidad_vacios=5, vacios_actuales=0,
    )


def _ccti(suf):
    return CD.objects.create(
        nombre=f"CCTI_{suf}", codigo=f"K{suf}", direccion="Av 2", comuna="San Bernardo",
        tipo='ccti', lat=-33.59, lng=-70.70, capacidad_vacios=10, vacios_actuales=0,
    )


class RetornoCCTITest(TestCase):
    """Un retorno a CCTI deja el contenedor en 'en_ccti' (lugar físico), sin 500."""

    def test_retorno_ccti_queda_en_ccti(self):
        suf = _sufijo()
        cd = _cd_cliente(suf)
        ccti = _ccti(suf)
        c = Container.objects.create(
            container_id=f"TST{suf.upper()}1", tipo='40', nave=f"N{suf}",
            cd_entrega=cd, estado='vacio',
        )
        c2 = EmptyReturnService.start(c, destination_type='ccti', destination_cd=ccti, user='regresion')
        c3 = EmptyReturnService.complete(c2, user='regresion')
        c3.refresh_from_db()
        self.assertEqual(c3.estado, 'en_ccti')
        # La vista marcar_devuelto ya no debe forzar 'devuelto' para destinos CCTI.
        self.assertEqual(c3.retorno_destino_tipo, 'ccti')
        # Forzar devuelto desde en_ccti sigue siendo inválido (FSM intacto).
        with self.assertRaises(ValidationError):
            c3.cambiar_estado('devuelto', 'regresion')

    def test_retorno_deposito_si_queda_devuelto(self):
        suf = _sufijo()
        cd = _cd_cliente(suf)
        c = Container.objects.create(
            container_id=f"TST{suf.upper()}2", tipo='20', nave=f"N{suf}",
            cd_entrega=cd, estado='vacio',
        )
        c2 = EmptyReturnService.start(c, destination_type='deposito', depot_name=f'Depo {suf}', user='regresion')
        c3 = EmptyReturnService.complete(c2, user='regresion')
        c3.refresh_from_db()
        self.assertEqual(c3.estado, 'devuelto')


class DesasignarCapacidadTest(TestCase):
    """Desasignar un conductor devuelve su capacidad del día."""

    def test_desasignar_devuelve_num_entregas(self):
        suf = _sufijo()
        cd = _cd_cliente(suf)
        d = Driver.objects.create(nombre=f"D {suf}", rut=f"{suf[:8]}", max_entregas_dia=3)
        c = Container.objects.create(
            container_id=f"TST{suf.upper()}3", tipo='40', nave=f"N{suf}",
            cd_entrega=cd, estado='liberado',
        )
        p = Programacion.objects.create(
            container=c, cd=cd, cliente='X',
            fecha_programada=timezone.now() + timedelta(hours=6),
        )
        p.asignar_conductor(d, 'regresion')
        d.refresh_from_db()
        self.assertEqual(d.num_entregas_dia, 1)
        # Flujo de la vista desasignar: liberar_conductor + limpiar driver.
        liberado = p.liberar_conductor()
        self.assertTrue(liberado)
        p.driver = None
        p.fecha_asignacion = None
        p.save(update_fields=['driver', 'fecha_asignacion'])
        d.refresh_from_db()
        self.assertEqual(d.num_entregas_dia, 0)


class ReversionFSMTest(TestCase):
    """Solo las reversiones explícitas pueden saltarse el FSM."""

    def test_devuelto_no_puede_revivir(self):
        suf = _sufijo()
        cd = _cd_cliente(suf)
        c = Container.objects.create(
            container_id=f"TST{suf.upper()}4", tipo='40', nave=f"N{suf}",
            cd_entrega=cd, estado='devuelto',
        )
        with self.assertRaises(ValidationError):
            c.cambiar_estado('por_arribar', 'regresion', permitir_reversion=True)

    def test_liberado_puede_revertir_a_por_arribar(self):
        suf = _sufijo()
        cd = _cd_cliente(suf)
        c = Container.objects.create(
            container_id=f"TST{suf.upper()}5", tipo='40', nave=f"N{suf}",
            cd_entrega=cd, estado='liberado',
        )
        c.cambiar_estado('por_arribar', 'regresion', permitir_reversion=True)
        c.refresh_from_db()
        self.assertEqual(c.estado, 'por_arribar')


class VendorNoBloqueaDespachoTest(TestCase):
    """Vendor vacío es advertencia (P2), no bloqueo (P0) del despacho automático."""

    def test_vendor_vacio_es_p2(self):
        from apps.core.services.anomaly_detector import AnomalyDetector
        suf = _sufijo()
        cd = _cd_cliente(suf)
        d = Driver.objects.create(nombre=f"D {suf}", rut=f"19{suf[:5]}", max_entregas_dia=3)
        c = Container.objects.create(
            container_id=f"TST{suf.upper()}6", tipo='40', nave=f"N{suf}",
            cd_entrega=cd, estado='liberado', peso_carga=2000,
            vendor='',  # vacío a propósito
        )
        p = Programacion.objects.create(
            container=c, cd=cd, cliente='X',
            fecha_programada=timezone.now() + timedelta(hours=6),
        )
        anomalias = AnomalyDetector.detect(p, d)
        vendor = [a for a in anomalias if a['code'] == 'ANOM_OPS_003']
        self.assertTrue(vendor, 'debería existir la anomalía de vendor')
        self.assertEqual(vendor[0]['severity'], 'P2')


class MantenimientoDiarioTest(TestCase):
    """El comando de mantenimiento diario resetea entregas y purga posiciones."""

    def test_resetea_entregas_y_purga_posiciones(self):
        from django.core.management import call_command
        from apps.drivers.models import DriverLocation
        suf = _sufijo()
        d = Driver.objects.create(nombre=f"M {suf}", rut=f"12{suf[:6]}", num_entregas_dia=4, max_entregas_dia=3)
        loc_vieja = DriverLocation.objects.create(driver=d, lat=-33.45, lng=-70.66)
        DriverLocation.objects.filter(pk=loc_vieja.pk).update(
            timestamp=timezone.now() - timedelta(days=90)
        )
        # entregas fuera de rango (>=4) y posición vieja de 90 días
        call_command('mantenimiento_diario')
        d.refresh_from_db()
        self.assertEqual(d.num_entregas_dia, 0)
        self.assertFalse(DriverLocation.objects.filter(pk=loc_vieja.pk).exists())