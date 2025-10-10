from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.drivers.models import Driver
from apps.routing.models import Route
from apps.routing.views import RouteViewSet


class RouteModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="driver_user",
            password="testpass123",
            first_name="Ana",
            last_name="Pérez",
        )
        self.driver = Driver.objects.create(
            nombre="Ana Pérez",
            rut="11111111-1",
            ppu="TEST01",
            tipo_conductor="LEASING",
            telefono="+56999999999",
        )

    def test_route_str_uses_driver_full_name(self):
        route = Route.objects.create(
            name="Ruta Matutina",
            driver=self.driver,
            route_date=date.today(),
            status="PLANNED",
        )

        label = str(route)
        expected_name = self.user.get_full_name()
        self.assertIn(expected_name, label)
        self.assertIn("Ruta Matutina", label)
        self.assertIn(str(route.route_date), label)

    def test_today_routes_view_returns_driver_payload(self):
        route = Route.objects.create(
            name="Ruta Hoy",
            driver=self.driver,
            route_date=timezone.localdate(),
            status="PLANNED",
        )

        factory = APIRequestFactory()
        request = factory.get("/api/routing/routes/today/")
        force_authenticate(request, user=self.user)
        view = RouteViewSet.as_view({"get": "today_routes"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        payload = response.data["routes"][0]
        self.assertEqual(payload["id"], str(route.id))
        self.assertEqual(payload["driver"]["name"], self.user.get_full_name())
