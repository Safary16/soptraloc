from unittest.mock import patch

import pandas as pd
from django.test import TestCase
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
