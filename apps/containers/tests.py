from unittest.mock import patch

import pandas as pd
from django.contrib import admin
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from django.utils import timezone
from django.core.management import call_command
from datetime import timedelta

from apps.cds.models import CD
from apps.containers.importers.embarque import EmbarqueImporter
from apps.containers.importers.programacion import ProgramacionImporter
from apps.containers.admin import ContainerAdmin
from apps.containers.models import Container
from apps.programaciones.models import Programacion
from apps.core.services.returns import EmptyReturnService
from apps.containers.serializers import ContainerListSerializer
from apps.clientes.models import ClienteEmpresa


class ContainerAdminClientCompanyTests(TestCase):
    def test_client_company_is_visible_editable_filterable_and_searchable(self):
        model_admin = ContainerAdmin(Container, admin.site)
        self.assertIn('cliente_empresa', model_admin.list_display)
        self.assertIn('cliente_empresa', model_admin.list_filter)
        self.assertIn('cliente_empresa', model_admin.autocomplete_fields)
        self.assertIn('cliente_empresa__nombre', model_admin.search_fields)
        delivery_fields = dict(model_admin.fieldsets)['Información de Entrega']['fields']
        self.assertIn('cliente_empresa', delivery_fields)

    def test_existing_container_can_be_repaired_with_client_company(self):
        company = ClienteEmpresa.objects.create(nombre='Empresa Container', rut='76.000.002-K')
        container = Container.objects.create(container_id='FIXU1234567', tipo='40', nave='Nave')
        container.cliente_empresa = company
        container.save(update_fields=['cliente_empresa', 'updated_at'])
        container.refresh_from_db()
        self.assertEqual(container.cliente_empresa, company)


class EmbarqueCustomerAssociationTests(TestCase):
    def setUp(self):
        self.empresa = ClienteEmpresa.objects.create(
            nombre='Comercial Peña y Compañía SpA', rut='76.123.456-7'
        )

    def _import(self, customer_header='Cliente', customer='comercial pena y compania spa'):
        frame = pd.DataFrame([{
            'Container Numbers': 'MSCU 123456-7',
            'Container Size': "40' HC",
            'Nave Confirmado': 'Nave Prueba',
            customer_header: customer,
        }])
        with patch(
            'apps.containers.importers.embarque.read_excel_with_header_detection',
            return_value=frame,
        ):
            return EmbarqueImporter('embarque.xlsx', 'test').procesar()

    def test_known_customer_is_normalized_and_linked_without_cd(self):
        result = self._import()
        container = Container.objects.get(container_id='MSCU1234567')
        self.assertEqual(result['creados'], 1)
        self.assertEqual(result['errores'], 0)
        self.assertEqual(container.cliente_empresa, self.empresa)
        self.assertEqual(container.cliente, 'comercial pena y compania spa')
        self.assertIsNone(container.cd_entrega)

    def test_customer_header_aliases_are_supported(self):
        result = self._import(customer_header='Consignee', customer='76.123.456-7')
        container = Container.objects.get(container_id='MSCU1234567')
        self.assertEqual(result['errores'], 0)
        self.assertEqual(container.cliente_empresa, self.empresa)
        self.assertIsNone(container.cd_entrega)

    def test_unknown_customer_is_explicit_and_not_created(self):
        result = self._import(customer='Cliente inexistente')
        self.assertEqual(result['creados'], 0)
        self.assertEqual(result['errores'], 1)
        self.assertFalse(Container.objects.exists())
        self.assertEqual(ClienteEmpresa.objects.count(), 1)
        self.assertIn('no está registrado', result['detalles'][0]['error'])

    def test_customer_column_is_required(self):
        frame = pd.DataFrame([{
            'Container Numbers': 'MSCU 123456-7',
            'Container Size': '40',
            'Nave Confirmado': 'Nave Prueba',
        }])
        with patch(
            'apps.containers.importers.embarque.read_excel_with_header_detection',
            return_value=frame,
        ):
            with self.assertRaisesRegex(Exception, "Columna requerida 'cliente'"):
                EmbarqueImporter('embarque.xlsx', 'test').procesar()


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

    def test_list_serializer_declares_each_field_once(self):
        fields = ContainerListSerializer.Meta.fields
        self.assertEqual(len(fields), len(set(fields)))

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
