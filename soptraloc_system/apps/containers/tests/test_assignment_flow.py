from __future__ import annotations

import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.containers.models import Container
from apps.drivers.models import Alert, Assignment, Driver, Location
from apps.containers.services.empty_inventory import get_empty_inventory_by_cd


class ContainerAssignmentFlowTests(APITestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            username="ops",
            password="secret",
            email="ops@example.com",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

        self.origin = Location.objects.create(
            name="CCTI Base",
            code="CCTI",
            address="Calle 1",
            city="Santiago",
            region="Metropolitana",
            country="Chile",
        )
        self.destination = Location.objects.create(
            name="CD El Peñón",
            code="CD_PENON",
            address="Dirección Peñón",
            city="San Bernardo",
            region="Metropolitana",
            country="Chile",
        )

        company = self._create_company()
        self.container = Container.objects.create(
            container_number="MSCU1234567",
            container_type="40ft",
            status="PROGRAMADO",
            owner_company=company,
            service_type="INDIRECTO_DEPOSITO",
            terminal=self.origin,
            cd_location="CD El Peñón",
            scheduled_date=timezone.localdate(),
            scheduled_time=(timezone.now() + timedelta(hours=1)).time(),
        )

        self.driver = Driver.objects.create(
            nombre="Juan Test",
            rut="11111111-1",
            telefono="+56911111111",
            ppu="AA-BB-11",
            tipo_conductor="LOCALERO",
            estado="OPERATIVO",
            ubicacion_actual="CCTI",
        )

    def _create_company(self):
        from apps.core.models import Company
        company, _ = Company.objects.get_or_create(
            code="CLIENTE-QA",
            defaults={
                "name": "Cliente QA",
                "rut": "12.345.678-9",
                "email": "cliente@example.com",
                "phone": "123456789",
                "address": "Calle Falsa 123",
            },
        )
        return company

    def test_assign_driver_via_api_sets_status_assigned(self):
        url = reverse("container-assign-driver", args=[self.container.id])
        response = self.client.post(url, {"driver_id": self.driver.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.container.refresh_from_db()
        self.driver.refresh_from_db()

        self.assertEqual(self.container.status, "ASIGNADO")
        self.assertEqual(self.container.conductor_asignado, self.driver)
        self.assertEqual(self.driver.contenedor_asignado, self.container)
        self.assertEqual(Assignment.objects.count(), 1)

    def test_mark_arrived_releases_driver_and_completes_assignment(self):
        self.test_assign_driver_via_api_sets_status_assigned()

        self.client.login(username="ops", password="secret")
        payload_start = {
            "container_id": str(self.container.id),
            "action": "start_route",
        }
        self.client.post(reverse("containers:update_status"), data=payload_start)

        now = timezone.now()
        payload_arrived = {
            "container_id": str(self.container.id),
            "action": "mark_arrived",
            "arrival_location": "CD_PENON",
        }
        response = self.client.post(reverse("containers:update_status"), data=payload_arrived)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.container.refresh_from_db()
        self.driver.refresh_from_db()
        assignment = Assignment.objects.get(container=self.container)

        self.assertIsNone(self.container.conductor_asignado)
        self.assertIsNone(self.driver.contenedor_asignado)
        self.assertEqual(self.driver.estado, "OPERATIVO")
        self.assertEqual(assignment.estado, "COMPLETADA")
        self.assertIsNotNone(assignment.fecha_completada)
        self.assertGreaterEqual(assignment.tiempo_real or 0, 0)
        self.assertGreaterEqual(assignment.ruta_minutos_real or 0, 0)

    def test_empty_inventory_counts_delivered_units(self):
        company = self._create_company()
        Container.objects.create(
            container_number="MSCU9999999",
            container_type="40ft",
            status="DESCARGADO_CD",
            owner_company=company,
            service_type="INDIRECTO_DEPOSITO",
            cd_location="CD El Peñón",
        )

        inventory = list(get_empty_inventory_by_cd())
        peñon_row = next(item for item in inventory if item.code == "CD_PENON")
        self.assertEqual(peñon_row.empty_count, 1)

        response = self.client.get(reverse("container-empty-inventory"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload_codes = {item["code"]: item["empty_count"] for item in response.json()["items"]}
        self.assertEqual(payload_codes.get("CD_PENON"), 1)

    def test_demurrage_alert_triggers_and_resolves_through_return_flow(self):
        self.container.demurrage_date = timezone.localdate() + timedelta(days=1)
        self.container.save(update_fields=["demurrage_date"])

        # Asignar conductor y preparar ruta de entrega
        self.test_assign_driver_via_api_sets_status_assigned()

        self.client.login(username="ops", password="secret")

        payload_start = {
            "container_id": str(self.container.id),
            "action": "start_route",
        }
        self.client.post(reverse("containers:update_status"), data=payload_start)

        payload_arrived = {
            "container_id": str(self.container.id),
            "action": "mark_arrived",
            "arrival_location": "CD_PENON",
        }
        self.client.post(reverse("containers:update_status"), data=payload_arrived)

        # Marcar descarga en CD
        update_status_url = reverse("containers:update_container_status", args=[self.container.id])
        response = self.client.post(
            update_status_url,
            data=json.dumps({"status": "DESCARGADO_CD"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.container.refresh_from_db()
        self.assertEqual(self.container.status, "DESCARGADO_CD")

        alert = Alert.objects.get(container=self.container, tipo="DEMURRAGE_PROXIMO")
        self.assertTrue(alert.is_active)
        self.assertEqual(alert.prioridad, "ALTA")

        # Disponer para devolución y asignar conductor nuevamente
        response = self.client.post(
            reverse("containers:mark_ready_for_return"),
            data=json.dumps({"container_id": str(self.container.id)}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.container.refresh_from_db()
        self.assertEqual(self.container.status, "DISPONIBLE_DEVOLUCION")

        response = self.client.post(
            reverse("containers:assign_return_driver"),
            data=json.dumps({
                "container_id": str(self.container.id),
                "driver_id": self.driver.id,
                "return_location": "CCTI",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Inicio de ruta de devolución
        response = self.client.post(
            reverse("containers:start_return_route"),
            data=json.dumps({"container_id": str(self.container.id)}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.container.refresh_from_db()
        self.assertEqual(self.container.status, "EN_RUTA_DEVOLUCION")

        # Finalizar contenedor devuelto
        response = self.client.post(
            reverse("containers:finalize_container"),
            data=json.dumps({
                "container_id": str(self.container.id),
                "has_eir": True,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.container.refresh_from_db()
        self.assertEqual(self.container.status, "FINALIZADO")

        self.assertFalse(
            Alert.objects.filter(
                container=self.container,
                tipo__in=["DEMURRAGE_PROXIMO", "DEMURRAGE_VENCIDO"],
                is_active=True,
            ).exists()
        )
