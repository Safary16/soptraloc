from unittest.mock import patch

import pandas as pd
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from django.utils import timezone
from django.core.management import call_command
from datetime import timedelta

from apps.cds.models import CD
from apps.containers.views import ContainerViewSet
from apps.containers.importers.programacion import ProgramacionImporter
from apps.containers.importers.embarque import EmbarqueImporter
from apps.containers.importers.liberacion import LiberacionImporter
from apps.containers.models import Container, Deposit, EvidenceDocument
from apps.programaciones.models import Programacion
from apps.core.services.returns import EmptyReturnService
from apps.core.utils import normalizar_cliente


class ProgramacionImporterBusinessFlowTests(TestCase):
    def setUp(self):
        self.cd = CD.objects.create(
            nombre='Destino Programación', codigo='DEST-01', direccion='Destino',
            comuna='Santiago', lat=-33.45, lng=-70.65,
        )

    def _import(self, container):
        frame = pd.DataFrame([{
            'Contenedor': container.container_id,
            'Fecha de Programacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
            'Centro Distribucion': self.cd.codigo,
            'Cliente': 'Cliente',
        }])
        with patch(
            'apps.containers.importers.programacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            return ProgramacionImporter('programacion.xlsx', 'test').procesar()

    def test_programacion_rejects_container_not_yet_released(self):
        container = Container.objects.create(
            container_id='WAIT1234567', estado='por_arribar', cliente='Cliente'
        )

        result = self._import(container)

        container.refresh_from_db()
        self.assertEqual(result['programados'], 0)
        self.assertEqual(result['errores'], 1)
        self.assertEqual(container.estado, 'por_arribar')
        self.assertFalse(Programacion.objects.filter(container=container).exists())

    def test_programacion_advances_released_container(self):
        container = Container.objects.create(
            container_id='FREE1234567', estado='liberado', cliente='Cliente',
            fecha_liberacion=timezone.now(),
        )

        result = self._import(container)

        container.refresh_from_db()
        self.assertEqual(result['programados'], 1)
        self.assertEqual(result['errores'], 0)
        self.assertEqual(container.estado, 'programado')
        self.assertTrue(Programacion.objects.filter(container=container).exists())


class ContainerCrudTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user('containerstaff', password='***', is_staff=True)
        self.payload = {
            'container_id': 'MSCU 123456-7', 'tipo': '40HC', 'tipo_carga': 'dry',
            'nave': 'Nave Prueba', 'estado': 'por_arribar', 'puerto': 'Valparaíso',
        }

    def test_public_reads_but_only_staff_mutates(self):
        self.assertEqual(self.client.get(reverse('container-list')).status_code, 200)
        self.assertIn(self.client.post(reverse('container-list'), self.payload, format='json').status_code, (401, 403))
        self.client.force_authenticate(self.staff)
        response = self.client.post(reverse('container-list'), self.payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['container_id'], 'MSCU1234567')

    def test_delete_cancels_and_preserves_container(self):
        container = Container.objects.create(container_id='CXLU1234567', tipo='40', nave='Nave')
        self.client.force_authenticate(self.staff)
        response = self.client.delete(reverse('container-detail', kwargs={'pk': container.pk}))
        self.assertEqual(response.status_code, 204)
        container.refresh_from_db()
        self.assertEqual(container.estado, 'cancelado')


class ScheduledReleaseTests(TestCase):
    def test_only_due_releases_are_advanced(self):
        due = Container.objects.create(
            container_id='DUEU1234567', tipo='40', nave='Nave', estado='por_arribar',
            fecha_liberacion=timezone.now() - timedelta(minutes=1),
        )
        future = Container.objects.create(
            container_id='FUTU1234567', tipo='40', nave='Nave', estado='por_arribar',
            fecha_liberacion=timezone.now() + timedelta(hours=1),
        )
        call_command('release_due_containers')
        due.refresh_from_db(); future.refresh_from_db()
        self.assertEqual(due.estado, 'liberado')
        self.assertEqual(future.estado, 'por_arribar')


class EmptyReturnFlowTests(TestCase):
    def setUp(self):
        self.origin = CD.objects.create(
            nombre='Patio origen', codigo='ORIGIN', direccion='Origen', comuna='Santiago',
            lat=-33.4, lng=-70.6, capacidad_vacios=5, vacios_actuales=1,
        )
        self.ccti = CD.objects.create(
            nombre='CCTI destino', codigo='CCTI-D', direccion='Destino', comuna='Santiago',
            tipo='ccti', lat=-33.5, lng=-70.7, capacidad_vacios=5,
        )
        self.container = Container.objects.create(
            container_id='RETU1234567', tipo='40', nave='Nave', estado='vacio',
            cd_entrega=self.origin, vacio_contabilizado=True,
        )

    def test_return_to_ccti_moves_inventory_between_locations(self):
        EmptyReturnService.start(
            self.container, destination_type='ccti', destination_cd=self.ccti, user='test'
        )
        self.container.refresh_from_db(); self.origin.refresh_from_db()
        self.assertEqual(self.container.estado, 'vacio_en_ruta')
        self.assertEqual(self.origin.vacios_actuales, 0)
        EmptyReturnService.complete(self.container, user='test')
        self.container.refresh_from_db(); self.ccti.refresh_from_db()
        self.assertEqual(self.container.estado, 'en_ccti')
        self.assertEqual(self.ccti.vacios_actuales, 1)
        self.assertTrue(self.container.vacio_contabilizado)

    def test_return_to_depot_closes_cycle(self):
        EmptyReturnService.start(
            self.container, destination_type='deposito', depot_name='Depósito Naviera', user='test'
        )
        EmptyReturnService.complete(self.container, user='test')
        self.container.refresh_from_db(); self.origin.refresh_from_db()
        self.assertEqual(self.container.estado, 'devuelto')
        self.assertEqual(self.origin.vacios_actuales, 0)
        self.assertFalse(self.container.vacio_contabilizado)

    def test_ccti_without_capacity_is_rejected_before_departure(self):
        self.ccti.capacidad_vacios = 0
        self.ccti.save(update_fields=['capacidad_vacios', 'updated_at'])
        with self.assertRaises(ValueError):
            EmptyReturnService.start(
                self.container, destination_type='ccti', destination_cd=self.ccti, user='test'
            )
        self.container.refresh_from_db(); self.origin.refresh_from_db()
        self.assertEqual(self.container.estado, 'vacio')
        self.assertEqual(self.origin.vacios_actuales, 1)


class ReglasNegocioImportadoresTests(TestCase):
    """Reglas de negocio de Seba (27-sep-2026) fijadas como tests:
    - El cliente se sube en la liberación; la programación hereda el del
      contenedor y el 'N/A' del Excel NUNCA lo pisa.
    - '45' en las planillas = 40' High Cube (40HC). Nunca se guarda '45'.
    - Las horas se suben HH:MM (o HH:MM:SS); un formato de hora ilegible
      produce error explícito, nunca 00:00:00 silencioso.
    - Las fechas se suben día/mes/año (dayfirst).
    """

    def setUp(self):
        self.cd = CD.objects.create(
            nombre='Destino Programación', codigo='DEST-01', direccion='Destino',
            comuna='Santiago', lat=-33.45, lng=-70.65,
        )

    def _importar_programacion(self, container, cliente_excel):
        frame = pd.DataFrame([{
            'Contenedor': container.container_id,
            'Fecha de Programacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
            'Centro Distribucion': self.cd.codigo,
            'Cliente': cliente_excel,
        }])
        with patch(
            'apps.containers.importers.programacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            return ProgramacionImporter('programacion.xlsx', 'test').procesar()

    # --- 1. Cliente se hereda de la liberación; 'N/A' nunca pisa ---

    def test_normalizar_cliente_na_devuelve_vacio(self):
        self.assertEqual(normalizar_cliente('N/A'), '')
        self.assertEqual(normalizar_cliente('NA'), '')
        self.assertEqual(normalizar_cliente('n/a'), '')
        self.assertEqual(normalizar_cliente('-'), '')

    def test_programacion_hereda_cliente_si_excel_dice_na(self):
        container = Container.objects.create(
            container_id='HEREDO123456', estado='liberado', cliente='Walmart',
            fecha_liberacion=timezone.now(),
        )
        result = self._importar_programacion(container, 'N/A')
        programa = Programacion.objects.get(container=container)
        self.assertEqual(result['programados'], 1)
        self.assertEqual(programa.cliente, 'Walmart')
        container.refresh_from_db()
        self.assertEqual(container.cliente, 'Walmart')

    def test_liberacion_sube_cliente_y_na_no_pisa_existente(self):
        container = Container.objects.create(
            container_id='LIBNA1234567', estado='por_arribar', cliente='Walmart',
        )
        frame = pd.DataFrame([{
            'contenedor': container.container_id,
            'almacen': 'TPS',
            'fecha salida': '01/10/2026',  # fecha fija pasada: timezone.now() es UTC y entre 21:00-24:00 local produce la fecha de mañana → por_arribar (HAL-27)
            'cliente': 'N/A',
        }])
        with patch(
            'apps.containers.importers.liberacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            result = LiberacionImporter('liberacion.xlsx', 'test').procesar()
        container.refresh_from_db()
        self.assertEqual(result['liberados'], 1)
        self.assertEqual(container.cliente, 'Walmart')

    def test_liberacion_sube_cliente_nuevo(self):
        container = Container.objects.create(
            container_id='LIBNV1234567', estado='por_arribar', cliente='',
        )
        frame = pd.DataFrame([{
            'contenedor': container.container_id,
            'almacen': 'TPS',
            'fecha salida': '01/10/2026',  # fecha fija pasada (mismo motivo HAL-27 que el test anterior)
            'cliente': 'Easy',
        }])
        with patch(
            'apps.containers.importers.liberacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            LiberacionImporter('liberacion.xlsx', 'test').procesar()
        container.refresh_from_db()
        self.assertEqual(container.cliente, 'Easy')

    # --- 2. 45 = 40HC ---

    def test_tipo_45_es_40hc(self):
        importer = EmbarqueImporter('embarque.xlsx', 'test')
        self.assertEqual(importer.validar_tipo('45'), '40HC')
        self.assertEqual(importer.validar_tipo('45H'), '40HC')
        self.assertEqual(importer.validar_tipo("45'"), '40HC')
        self.assertEqual(importer.validar_tipo('45 HC'), '40HC')
        self.assertEqual(importer.validar_tipo('40HC'), '40HC')
        self.assertEqual(importer.validar_tipo('20'), '20')

    def test_programacion_med_45_es_40hc(self):
        container = Container.objects.create(
            container_id='MED45123456', estado='liberado', cliente='Walmart',
            fecha_liberacion=timezone.now(),
        )
        frame = pd.DataFrame([{
            'Contenedor': container.container_id,
            'Fecha de Programacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
            'Centro Distribucion': self.cd.codigo,
            'Cliente': 'Walmart',
            'med': '45',
            'tipo': 'H',
        }])
        with patch(
            'apps.containers.importers.programacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            ProgramacionImporter('programacion.xlsx', 'test').procesar()
        container.refresh_from_db()
        self.assertEqual(container.tipo, '40HC')

    # --- 3. Hora HH:MM entra (liberación y programación) ---

    def test_liberacion_hora_hh_mm(self):
        container = Container.objects.create(
            container_id='LIBHH1234567', estado='por_arribar', cliente='Walmart',
        )
        frame = pd.DataFrame([{
            'contenedor': container.container_id,
            'almacen': 'TPS',
            'fecha salida': '26/09/2026',
            'hora salida': '14:30',
        }])
        with patch(
            'apps.containers.importers.liberacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            LiberacionImporter('liberacion.xlsx', 'test').procesar()
        container.refresh_from_db()
        self.assertEqual(timezone.localtime(container.fecha_liberacion).hour, 14)
        self.assertEqual(timezone.localtime(container.fecha_liberacion).minute, 30)

    def test_programacion_hora_hh_mm(self):
        container = Container.objects.create(
            container_id='PROGHH123456', estado='liberado', cliente='Walmart',
            fecha_liberacion=timezone.now(),
        )
        frame = pd.DataFrame([{
            'Contenedor': container.container_id,
            'Fecha de Programacion': '26/09/2026',
            'Centro Distribucion': self.cd.codigo,
            'Cliente': 'Walmart',
            'hora': '14:30',
        }])
        with patch(
            'apps.containers.importers.programacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            ProgramacionImporter('programacion.xlsx', 'test').procesar()
        programa = Programacion.objects.get(container=container)
        self.assertEqual(timezone.localtime(programa.fecha_programada).hour, 14)
        self.assertEqual(timezone.localtime(programa.fecha_programada).minute, 30)

    # --- 4. Día/mes/año (dayfirst): 05/10/2026 es 5 de octubre ---

    def test_liberacion_fecha_dayfirst(self):
        container = Container.objects.create(
            container_id='LIBAÑO123456', estado='por_arribar', cliente='Walmart',
        )
        frame = pd.DataFrame([{
            'contenedor': container.container_id,
            'almacen': 'TPS',
            'fecha salida': '05/10/2026',
        }])
        with patch(
            'apps.containers.importers.liberacion.read_excel_with_header_detection',
            return_value=frame,
        ):
            LiberacionImporter('liberacion.xlsx', 'test').procesar()
        container.refresh_from_db()
        self.assertEqual(container.fecha_liberacion.day, 5)
        self.assertEqual(container.fecha_liberacion.month, 10)



# ===== Trabajo 1: export de stock completo =====
class ExportStockCompletoTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='op', password='x12345', is_staff=True)
        self.client.force_authenticate(user=self.user)
        Container.objects.create(container_id='TEST0001', tipo='40HC', estado='por_arribar')
        Container.objects.create(container_id='TEST0002', tipo='40HC', estado='secuenciado')
        Container.objects.create(container_id='TEST0003', tipo='40HC', estado='devuelto')

    def test_default_retrocompatible(self):
        """Sin parámetros: solo liberado y por_arribar (comportamiento histórico)."""
        resp = self.client.get('/api/containers/export-stock/')
        self.assertEqual(resp.status_code, 200)
        ids = [c['container_id'] for c in resp.data['containers']]
        self.assertIn('TEST0001', ids)
        self.assertNotIn('TEST0003', ids)

    def test_incluir_todos_devuelve_devueltos(self):
        """incluir_todos=true: un contenedor devuelto SÍ aparece."""
        resp = self.client.get('/api/containers/export-stock/?incluir_todos=true')
        self.assertEqual(resp.status_code, 200)
        ids = [c['container_id'] for c in resp.data['containers']]
        self.assertIn('TEST0003', ids)
        self.assertIn('TEST0002', ids)
        self.assertEqual(resp.data['total'], 3)

    def test_estado_parametro(self):
        resp = self.client.get('/api/containers/export-stock/?estado=devuelto')
        self.assertEqual(resp.status_code, 200)
        ids = [c['container_id'] for c in resp.data['containers']]
        self.assertEqual(ids, ['TEST0003'])

    def test_estado_invalido_400(self):
        resp = self.client.get('/api/containers/export-stock/?estado=inexistente')
        self.assertEqual(resp.status_code, 400)


# ===== Trabajo 2: EvidenceDocument =====
class EvidenceDocumentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='op', password='x12345', is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.cont = Container.objects.create(container_id='TEST0004', tipo='40HC', estado='devuelto')

    def _upload(self, contenido=b'PDF-EVIDENCIA', nombre='eir.pdf', fuente='Depósito X'):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return self.client.post(
            f'/api/containers/{self.cont.pk}/evidencias/',
            {'archivo': SimpleUploadedFile(nombre, contenido), 'tipo': 'eir_out', 'fuente': fuente},
            format='multipart'
        )

    def test_subida_y_md5(self):
        resp = self._upload()
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.data['duplicado'])
        doc = EvidenceDocument.objects.get(pk=resp.data['evidencia']['id'])
        import hashlib
        self.assertEqual(doc.md5, hashlib.md5(b'PDF-EVIDENCIA').hexdigest())
        self.assertEqual(doc.fuente, 'Depósito X')

    def test_duplicado_marcado_no_crash(self):
        r1 = self._upload()
        r2 = self._upload(nombre='copia.pdf')
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        self.assertTrue(r2.data['duplicado'])
        self.assertEqual(r2.data['evidencia']['duplicado_de'], r1.data['evidencia']['id'])

    def test_sin_archivo_400(self):
        resp = self.client.post(f'/api/containers/{self.cont.pk}/evidencias/', {}, format='multipart')
        self.assertEqual(resp.status_code, 400)

    def test_listado_por_contenedor(self):
        self._upload()
        resp = self.client.get(f'/api/containers/{self.cont.pk}/evidencias/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['total'], 1)


# ===== Trabajo 3: Deposit + verificación externa =====
class DepositYVerificacionTests(TestCase):
    def setUp(self):
        self.cont = Container.objects.create(
            container_id='TEST0005', tipo='40HC', estado='por_arribar',
            deposito_devolucion='Depósito Alfa'
        )
        self.dep = Deposit.objects.create(name='Depósito Alfa', aliases='DEP ALFA, deposito alfa')

    def test_resolver_por_nombre_y_alias(self):
        self.assertEqual(Deposit.resolver('depósito alfa'), self.dep)
        self.assertEqual(Deposit.resolver('DEP ALFA'), self.dep)
        self.assertIsNone(Deposit.resolver('Otro Depósito'))
        self.assertIsNone(Deposit.resolver(None))

    def test_verificacion_divergencia(self):
        """Estado declarado por_arribar, externo confirma devuelto → divergencia."""
        out = self.cont.marcar_verificacion_externa('devuelto', 'Portal Depósito', 'DEP ALFA')
        self.assertTrue(out['divergencia'])
        self.cont.refresh_from_db()
        self.assertEqual(self.cont.estado, 'por_arribar')  # FSM intacto
        self.assertEqual(self.cont.estado_verificado, 'devuelto')
        self.assertEqual(self.cont.deposito_verificado, self.dep)
        self.assertTrue(self.cont.divergencia_estado)

    def test_verificacion_sin_divergencia(self):
        out = self.cont.marcar_verificacion_externa('por_arribar', 'Portal Depósito')
        self.assertFalse(out['divergencia'])
        self.cont.refresh_from_db()
        self.assertIsNone(self.cont.deposito_verificado)
        self.assertFalse(self.cont.divergencia_estado)

    def test_estado_externo_invalido(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.cont.marcar_verificacion_externa('no_existe', 'Portal')

    def test_evento_registrado(self):
        from apps.events.models import Event
        self.cont.marcar_verificacion_externa('devuelto', 'Portal Depósito')
        self.assertTrue(Event.objects.filter(
            container=self.cont,
            detalles__tipo='verificacion_externa',
            detalles__divergencia=True
        ).exists())


# ---------------------------------------------------------------------------
# FASE 5 — HAL-26: idempotencia unificada de soltar_contenedor (operador).
# Antes: reintento tras drop → 400 engañoso; el endpoint del conductor sí era
# idempotente (y por HAL-20 reventaba). Ahora ambos espejan el contrato.
# ---------------------------------------------------------------------------

class Hal26SoltarContenedorIdempotenteTests(TestCase):
    """HAL-26: reintento de soltar_contenedor (operador) → 200 ya_registrado."""

    def setUp(self):
        from apps.programaciones.models import Programacion
        from apps.drivers.models import Driver
        self.operador = User.objects.create_user(username='op26', password='***', is_staff=True)
        self.driver = Driver.objects.create(nombre='HAL26 Driver')
        self.cd = CD.objects.create(
            nombre='HAL26 CD', codigo='HAL26-CD', direccion='CD',
            comuna='Santiago', lat=-33.45, lng=-70.65,
            permite_soltar_contenedor=True,
        )
        self.container = Container.objects.create(
            container_id='HAL26S1234', estado='soltado', cliente='HAL26 Cliente',
            cd_entrega=self.cd,
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='HAL26 Cliente', fecha_programada=timezone.now(),
        )
        self.factory = APIRequestFactory()

    def test_reintento_soltado_200_idempotente(self):
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=self.operador)
        view = ContainerViewSet.as_view({'post': 'soltar_contenedor'})
        response = view(request, pk=self.container.pk)
        self.assertEqual(response.status_code, 200,
                         f'reintento debe ser 200 idempotente: {response.data}')
        self.assertTrue(response.data.get('ya_registrado'))

    def test_estado_distinto_sigue_400(self):
        self.container.estado = 'en_ruta'
        self.container.save()
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=self.operador)
        view = ContainerViewSet.as_view({'post': 'soltar_contenedor'})
        response = view(request, pk=self.container.pk)
        self.assertEqual(response.status_code, 400)
