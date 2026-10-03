"""
Tests JWT (Fase 2 plan soptraloc↔OpenClaw).

Contrato clave: JWT es ADICIONAL — SessionAuth y AllowAny permanecen intactos.
Estos tests verifican que (1) los endpoints de token existen y funcionan,
(2) el acceso anónimo a la API sigue funcionando SIN token (regla sagrada).
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


class JWTAuthTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='jwt_tester', password='pass-test-1234'
        )

    def test_token_obtain_ok(self):
        r = self.client.post('/api/token/', {'username': 'jwt_tester', 'password': 'pass-test-1234'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)
        self.assertIn('refresh', r.data)

    def test_token_obtain_bad_password_401(self):
        r = self.client.post('/api/token/', {'username': 'jwt_tester', 'password': 'wrong'})
        self.assertEqual(r.status_code, 401)

    def test_token_refresh_ok(self):
        obtain = self.client.post('/api/token/', {'username': 'jwt_tester', 'password': 'pass-test-1234'})
        r = self.client.post('/api/token/refresh/', {'refresh': obtain.data['refresh']})
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)

    def test_token_verify_ok(self):
        obtain = self.client.post('/api/token/', {'username': 'jwt_tester', 'password': 'pass-test-1234'})
        r = self.client.post('/api/token/verify/', {'token': obtain.data['access']})
        self.assertEqual(r.status_code, 200)

    def test_anonymous_api_access_still_works(self):
        """REGLA SAGRADA: AllowAny intacto — la API sigue accesible sin token."""
        r = self.client.get('/api/containers/')
        self.assertEqual(r.status_code, 200)

    def test_bearer_token_accepted_on_api(self):
        """Un cliente con Bearer válido también puede consultar (auth adicional)."""
        obtain = self.client.post('/api/token/', {'username': 'jwt_tester', 'password': 'pass-test-1234'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {obtain.data['access']}")
        r = self.client.get('/api/containers/')
        self.assertEqual(r.status_code, 200)
