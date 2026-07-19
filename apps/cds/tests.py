from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import CD

# Create your tests here.


class CDMasterDataCrudTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user('cdstaff', password='StrongPass123!', is_staff=True)
        self.payload = {
            'nombre': 'CD Prueba', 'codigo': 'CD-01', 'direccion': 'Calle 1',
            'comuna': 'Santiago', 'tipo': 'cliente', 'lat': '-33.450000',
            'lng': '-70.650000', 'tiempo_promedio_descarga_min': 45,
            'geocerca_radio_m': 250, 'activo': True,
        }

    def test_public_can_list_but_cannot_mutate(self):
        self.assertEqual(self.client.get(reverse('cd-list')).status_code, 200)
        self.assertIn(self.client.post(reverse('cd-list'), self.payload, format='json').status_code, (401, 403))

    def test_staff_crud_and_delete_is_soft(self):
        self.client.force_authenticate(self.staff)
        created = self.client.post(reverse('cd-list'), self.payload, format='json')
        self.assertEqual(created.status_code, 201)
        pk = created.data['id']
        updated = self.client.patch(reverse('cd-detail', kwargs={'pk': pk}), {'geocerca_radio_m': 300}, format='json')
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data['geocerca_radio_m'], 300)
        self.assertEqual(self.client.delete(reverse('cd-detail', kwargs={'pk': pk})).status_code, 204)
        self.assertFalse(CD.objects.get(pk=pk).activo)
