from __future__ import annotations

from datetime import timedelta
from io import BytesIO

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.containers.models import Container
from apps.containers.services.excel_importers import (
    apply_programming,
    apply_release_schedule,
    import_vessel_manifest,
)
from apps.drivers.models import Alert

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def dataframe_to_excel(dataframe: pd.DataFrame, filename: str) -> BytesIO:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False)
    buffer.seek(0)
    buffer.name = filename
    return buffer


def build_manifest_file(container_number: str = "MSCU1234567") -> BytesIO:
    today = timezone.now().date().strftime("%d/%m/%Y")
    df = pd.DataFrame(
        [
            {
                "Nave Confirmado": "APL CHARLESTON",
                "Viaje Confirmado": "APL1234",
                "ETA Confirmada": today,
                "Destino": "San Antonio",
                "Container Numbers": container_number,
                "Container Size": "40HC",
                "Container Seal": "SEL123",
                "Weight Kgs": "24000",
                "Vendor": "Walmart",
                "Carrier": "CMA CGM",
                "Agencia": "Agencia Uno",
            }
        ]
    )
    return dataframe_to_excel(df, "manifest.xlsx")


def build_release_file(container_number: str = "MSCU1234567") -> BytesIO:
    today = timezone.now().date().strftime("%d/%m/%Y")
    df = pd.DataFrame(
        [
            {
                "Contenedor": container_number,
                "Fecha Salida": today,
                "Hora Salida": "08:30",
                "Devolucion Vacio": "DEP TEST",
                "Almacen": "ALM 1",
            }
        ]
    )
    return dataframe_to_excel(df, "release.xlsx")


def build_program_file(container_number: str = "MSCU1234567") -> BytesIO:
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    df = pd.DataFrame(
        [
            {
                "Contenedor": container_number,
                "Fecha Programacion": tomorrow.strftime("%d/%m/%Y"),
                "Hora Programacion": "09:45",
                "Destino": "CD Quilicura",
                "Demurrage": today.strftime("%d/%m/%Y"),
                "Deposito": "DEP TEST",
                "Tipo Contenedor": "40HC",
            }
        ]
    )
    return dataframe_to_excel(df, "program.xlsx")


class ExcelImporterServiceTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tester",
            password="secret123",
            email="tester@example.com",
        )

    def test_manifest_import_creates_container(self):
        manifest_file = build_manifest_file()
        summaries = import_vessel_manifest([manifest_file], self.user)

        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary.created, 1)
        self.assertEqual(summary.updated, 0)
        container = Container.objects.get(container_number="MSCU 123456-7")
        self.assertEqual(container.status, "POR_ARRIBAR")
        self.assertEqual(container.shipping_line.name, "CMA CGM")
        self.assertEqual(container.owner_company.name, "Walmart")

    def test_release_import_updates_container(self):
        import_vessel_manifest([build_manifest_file()], self.user)
        container = Container.objects.get(container_number="MSCU 123456-7")

        release_summary = apply_release_schedule(build_release_file(), self.user)
        self.assertEqual(release_summary.updated, 1)

        container.refresh_from_db()
        self.assertEqual(container.status, "LIBERADO")
        self.assertIsNotNone(container.release_date, "La fecha de liberación debería estar guardada")
        self.assertIsNotNone(container.release_time, "La hora de liberación debería estar guardada")
        self.assertEqual(container.release_date, timezone.now().date(), "La fecha debe ser hoy")
        self.assertEqual(str(container.release_time), "08:30:00", "La hora debe ser 08:30")
        self.assertEqual(container.deposit_return, "DEP TEST")
        self.assertEqual(container.storage_location, "ALM 1")

    def test_programming_import_sets_schedule_and_alert(self):
        import_vessel_manifest([build_manifest_file()], self.user)
        container = Container.objects.get(container_number="MSCU 123456-7")

        summary = apply_programming(build_program_file(), self.user)
        self.assertEqual(summary.updated, 1)

        container.refresh_from_db()
        self.assertEqual(container.status, "PROGRAMADO")
        self.assertEqual(container.cd_location, "CD QUILICURA")
        self.assertIsNotNone(container.scheduled_date, "La fecha de programación debería estar guardada")
        self.assertIsNotNone(container.scheduled_time, "La hora de programación debería estar guardada")
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.assertEqual(container.scheduled_date, tomorrow, "La fecha debe ser mañana")
        self.assertEqual(str(container.scheduled_time), "09:45:00", "La hora debe ser 09:45")

        self.assertTrue(
            Alert.objects.filter(
                container=container,
                tipo="DEMURRAGE_PROXIMO",
                is_active=True,
            ).exists()
        )


class ContainerImportApiTests(APITestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            username="apitester",
            password="secret123",
            email="api@example.com",
        )
        self.client.force_authenticate(user=self.user)

    def _upload_file(self, buffer: BytesIO, name: str) -> SimpleUploadedFile:
        return SimpleUploadedFile(name, buffer.getvalue(), content_type=EXCEL_MIME)

    def test_import_manifest_endpoint_creates_container(self):
        manifest = build_manifest_file()
        response = self.client.post(
            reverse('container-import-manifest'),
            data={'files': [self._upload_file(manifest, 'manifest.xlsx')]},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Container.objects.count(), 1)
        payload = response.json()
        self.assertEqual(payload['summaries'][0]['created'], 1)

    def test_release_and_programming_endpoints_update_container(self):
        manifest = build_manifest_file()
        self.client.post(
            reverse('container-import-manifest'),
            data={'files': [self._upload_file(manifest, 'manifest.xlsx')]},
            format='multipart',
        )

        release = build_release_file()
        response_release = self.client.post(
            reverse('container-import-release'),
            data={'files': [self._upload_file(release, 'release.xlsx')]},
            format='multipart',
        )
        self.assertEqual(response_release.status_code, status.HTTP_200_OK)

        program = build_program_file()
        response_program = self.client.post(
            reverse('container-import-programming'),
            data={'files': [self._upload_file(program, 'program.xlsx')]},
            format='multipart',
        )
        self.assertEqual(response_program.status_code, status.HTTP_200_OK)

        container = Container.objects.get(container_number="MSCU 123456-7")
        self.assertEqual(container.status, "PROGRAMADO")
        self.assertIsNotNone(container.scheduled_date)

    def test_export_liberated_endpoint_returns_excel(self):
        manifest = build_manifest_file()
        self.client.post(
            reverse('container-import-manifest'),
            data={'files': [self._upload_file(manifest, 'manifest.xlsx')]},
            format='multipart',
        )

        release = build_release_file()
        self.client.post(
            reverse('container-import-release'),
            data={'files': [self._upload_file(release, 'release.xlsx')]},
            format='multipart',
        )

        response = self.client.get(reverse('container-export-liberated'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], EXCEL_MIME)
        self.assertGreater(len(response.content), 0)
        self.assertIn('attachment;', response['Content-Disposition'])
