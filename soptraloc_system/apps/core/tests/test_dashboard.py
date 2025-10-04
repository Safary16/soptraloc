from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


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
