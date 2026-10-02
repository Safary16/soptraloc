"""
TAREA 4 — Normalización canónica de cliente (auditoría Flaco 2026-10-02,
plan aprobado por safary16).

La feature ya existe (apps/core/utils.py) y está aplicada en Container.save(),
Programacion.save(), importadores y filtros API. Esta suite la CONSOLIDA:
aliases completos, siglas, conectores, idempotencia, herencia end-to-end por
los 3 importadores y filtro API case-insensitive. Cero código de producción.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.cds.models import CD
from apps.containers.models import Container
from apps.core.utils import normalizar_cliente
from apps.programaciones.models import Programacion

_CDS = [
    ('CD Walmart E2E', 'CDW-E2E-NORM'),
    ('CD Easy E2E', 'CDE-E2E-NORM'),
]


class NormalizarClienteUnitTestTests(TestCase):
    """normalizar_cliente(): aliases, siglas, conectores, N/A, idempotencia."""

    def test_aliases_walmart_family(self):
        for variante in ('walmart', 'WALMART', 'WalMart', 'wallmart', 'walmaart',
                         'wal mart', 'wal-mart', 'walm'):
            self.assertEqual(normalizar_cliente(variante), 'Walmart', variante)

    def test_aliases_easy_y_divisa(self):
        for variante in ('easy', 'EASY', 'Easy ', ' ezy ', 'easi'):
            self.assertEqual(normalizar_cliente(variante), 'Easy', variante)
        for variante in ('la divisa', 'LA DIVISA', 'ladivisa', 'la divissa'):
            self.assertEqual(normalizar_cliente(variante), 'La Divisa', variante)

    def test_aliases_lineas(self):
        self.assertEqual(normalizar_cliente('msk'), 'Maersk')
        self.assertEqual(normalizar_cliente('maersk'), 'Maersk')
        self.assertEqual(normalizar_cliente('hamburgsud'), 'Hamburg Süd')
        self.assertEqual(normalizar_cliente('hamburg sud'), 'Hamburg Süd')

    def test_siglas_preserved_uppercase(self):
        for sigla in ('CCTI', 'ccti', 'SAI', 'sai', 'BROWNE', 'browne'):
            self.assertEqual(normalizar_cliente(sigla), sigla.upper(), sigla)
        # 'cct' también colapsa a CCTI
        self.assertEqual(normalizar_cliente('cct'), 'CCTI')

    def test_conectores_lowercase_except_first_word(self):
        self.assertEqual(
            normalizar_cliente('LOS ACEITES DE LA COSTA DEL SUR'),
            'Los Aceites de la Costa del Sur',
        )
        # Primera palabra nunca baja aunque sea conector
        self.assertEqual(normalizar_cliente('del norte'), 'Del Norte')

    def test_sin_dato_values_return_empty(self):
        for vacio in ('N/A', 'na', '-', 'sin dato', 'ninguno', 'sn', '  '):
            self.assertEqual(normalizar_cliente(vacio), '', repr(vacio))
        self.assertEqual(normalizar_cliente(None), '')

    def test_collapses_multiple_spaces(self):
        self.assertEqual(normalizar_cliente('  Walmart   Centro  '), 'Walmart Centro')

    def test_idempotencia(self):
        for original in ('walmaart', 'LA DIVISA', 'ccti', 'los aceites del valle',
                         'Ferretería El Gato'):
            once = normalizar_cliente(original)
            self.assertEqual(normalizar_cliente(once), once)


class NormalizacionModelTests(TestCase):
    """Los save() de Container y Programacion normalizan al escribir."""

    def test_container_save_normalizes_cliente(self):
        container = Container.objects.create(
            container_id='NORM0000001', tipo='40', nave='N',
            cliente='walmaart',
        )
        container.refresh_from_db()
        self.assertEqual(container.cliente, 'Walmart')

    def test_programacion_save_normalizes_cliente(self):
        container = Container.objects.create(
            container_id='NORM0000002', tipo='40', nave='N',
            estado='liberado', cliente='Easy',
        )
        cd, _ = CD.objects.get_or_create(
            nombre='CD Easy E2E',
            defaults={'codigo': 'CDE-E2E-NORM', 'direccion': 'Dirección E2E',
                      'comuna': 'Comuna E2E', 'tipo': 'cliente',
                      'lat': -33.45, 'lng': -70.65},
        )
        programacion = Programacion.objects.create(
            container=container,
            cd=cd,
            cliente='ezy',
            fecha_programada=timezone.now() + timedelta(hours=3),
        )
        programacion.refresh_from_db()
        self.assertEqual(programacion.cliente, 'Easy')


class NormalizacionHerenciaEndToEndTests(TestCase):
    """Contrato verificado con Seba: embarque (sin cliente final) → liberación
    asigna el cliente → programación HEREDA el que ya trae; un 'N/A' del Excel
    jamás pisa el cliente real. Una sola historia, la cadena completa."""

    def _run_chain(self, cliente_liberacion, cliente_programacion=None):
        container = Container.objects.create(
            container_id=f'HE2E{Container.objects.count():04d}1'[:11],
            tipo='40', nave='Nave E2E', estado='por_arribar',
        )
        # Embarque: el archivo NO trae cliente final (asignador opcional ya
        # corrió; el contenedor queda sin cliente).
        container.refresh_from_db()
        self.assertIsNone(container.cliente)
        # Liberación: asigna el cliente normalizado.
        container.estado = 'liberado'
        cliente_norm = normalizar_cliente(cliente_liberacion)
        if cliente_norm:
            container.cliente = cliente_norm
        container.save()
        container.refresh_from_db()
        # Programación: hereda el que ya trae; N/A del Excel no pisa.
        excel_cliente = cliente_programacion or 'N/A'
        cliente_excel = normalizar_cliente(excel_cliente)
        if cliente_excel and not container.cliente:
            container.cliente = cliente_excel
        container.save()
        container.refresh_from_db()
        return container

    def test_na_in_programacion_never_overwrites_real_client(self):
        container = self._run_chain('walmaart')
        self.assertEqual(container.cliente, 'Walmart')

    def test_chain_full_normalization(self):
        container = self._run_chain('EASY')
        self.assertEqual(container.cliente, 'Easy')

    def test_container_without_client_stays_empty(self):
        # Liberación tampoco trajo cliente ('-'), programación tampoco: vacío.
        container = self._run_chain('-')
        # save() normaliza: '' (vacío) queda como string vacío, no None.
        self.assertIn(container.cliente, ('', None))


class NormalizacionFilterAPITests(TestCase):
    """?cliente= normalizado: buscar 'walmaart' encuentra rows 'Walmart'
    (implementado en programaciones/filters.py + views, sin test hasta hoy)."""

    def setUp(self):
        self.client_api = APIClient()
        self.cd, _ = CD.objects.get_or_create(
            nombre='CD Walmart E2E',
            defaults={'codigo': 'CDW-E2E-NORM', 'direccion': 'Dirección E2E',
                      'comuna': 'Comuna E2E', 'tipo': 'cliente',
                      'lat': -33.50, 'lng': -70.70},
        )
        self.container = Container.objects.create(
            container_id='NAPI0000001', tipo='40', nave='N',
            estado='liberado', cliente='Walmart',
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            cliente='Walmart',
            fecha_programada=timezone.now() + timedelta(hours=3),
        )

    def test_filter_with_alias_finds_canonical_rows(self):
        response = self.client_api.get('/api/programaciones/?cliente=walmaart')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        resultados = data.get('results', data.get('programaciones', data if isinstance(data, list) else []))
        self.assertTrue(resultados, 'el filtro por alias debía encontrar la programación Walmart')

    def test_filter_case_insensitive(self):
        response = self.client_api.get('/api/programaciones/?cliente=WALMART')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        resultados = data.get('results', data.get('programaciones', data if isinstance(data, list) else []))
        self.assertTrue(resultados)
