from unittest.mock import patch

import pandas as pd
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from django.utils import timezone

from apps.cds.models import CD
from apps.containers.importers.programacion import ProgramacionImporter
from apps.containers.models import Container
from apps.programaciones.models import Programacion


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
