from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.containers.models import Container
from apps.core.models import Company
from apps.drivers.models import Alert, Location


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

    def test_dashboard_loads_without_data(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard - Contenedores")

    def test_dashboard_generates_unassigned_alerts(self):
        self.client.login(username="admin", password="admin123")

        location = Location.objects.create(
            name="CD Quilicura",
            code="CD_QUILICURA",
            address="Calle CD",
            city="Santiago",
            region="Metropolitana",
            country="Chile",
        )
        company = Company.objects.create(
            name="Cliente Alert",
            code="CLIENTE-ALERT",
            rut="76.543.210-9",
            email="alert@example.com",
            phone="1234567",
            address="Dirección",
        )

        Container.objects.create(
            container_number="APZU1234567",
            container_type="40ft",
            status="PROGRAMADO",
            owner_company=company,
            service_type="INDIRECTO_DEPOSITO",
            cd_location="CD Quilicura",
            scheduled_date=timezone.localdate(),
            scheduled_time=(timezone.now() + timedelta(hours=1)).time(),
            terminal=location,
        )

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Alert.objects.filter(tipo="CONTENEDOR_SIN_ASIGNAR", is_active=True).exists(),
            "Debe generarse alerta para contenedor programado sin conductor",
        )
