from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from apps.core.models import Company, Vehicle, MovementCode


class CoreAPITestCase(APITestCase):
    """Escenarios básicos para validar los endpoints principales de Core."""

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret")
        self.client.force_authenticate(self.user)

    def test_create_company(self):
        payload = {
            "name": "Soptra Logistics",
            "code": "SOP-01",
            "rut": "12345678-9",
            "email": "contacto@soptra.local",
            "phone": "+56 9 9999 9999",
            "address": "Camino Internacional 123",
        }

        response = self.client.post("/api/v1/core/companies/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Company.objects.filter(code="SOP-01").exists())
        company = Company.objects.get(code="SOP-01")
        self.assertEqual(company.created_by, self.user)

    def test_vehicle_available_endpoint(self):
        # Vehículo disponible
        available_vehicle = Vehicle.objects.create(
            plate="AA-BB-11",
            vehicle_type="truck",
            brand="Volvo",
            model="FH",
            year=2023,
            status="available",
            max_capacity="18.50",
        )

        # Vehículo no disponible
        Vehicle.objects.create(
            plate="CC-DD-22",
            vehicle_type="truck",
            brand="Scania",
            model="R500",
            year=2021,
            status="maintenance",
            max_capacity="16.00",
        )

        response = self.client.get("/api/v1/core/vehicles/available/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["plate"], available_vehicle.plate)

    def test_movement_code_generate_and_use(self):
        response = self.client.post(
            "/api/v1/core/movement-codes/generate/",
            {"movement_type": "load"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        code_value = response.data["code"]
        movement_code = MovementCode.objects.get(code=code_value)
        self.assertEqual(movement_code.created_by, self.user)
        self.assertIsNone(movement_code.used_at)

        use_response = self.client.patch(f"/api/v1/core/movement-codes/{movement_code.pk}/use_code/")

        self.assertEqual(use_response.status_code, status.HTTP_200_OK)
        movement_code.refresh_from_db()
        self.assertIsNotNone(movement_code.used_at)
        self.assertEqual(movement_code.updated_by, self.user)

    def test_movement_code_generate_invalid_type(self):
        response = self.client.post(
            "/api/v1/core/movement-codes/generate/",
            {"movement_type": "invalid"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
