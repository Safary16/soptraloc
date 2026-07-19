from django.contrib import admin
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.clientes.models import ClienteEmpresa
from .admin import CDAdmin
from .models import CD

class CDAdminClientCompanyTests(TestCase):
    def test_client_company_is_visible_editable_filterable_and_searchable(self):
        model_admin = CDAdmin(CD, admin.site)
        self.assertIn('cliente_empresa', model_admin.list_display)
        self.assertIn('cliente_empresa', model_admin.list_filter)
        self.assertIn('cliente_empresa', model_admin.autocomplete_fields)
        self.assertIn('cliente_empresa__nombre', model_admin.search_fields)
        basic_fields = dict(model_admin.fieldsets)['Información Básica']['fields']
        self.assertIn('cliente_empresa', basic_fields)

    def test_admin_form_persists_client_company(self):
        company = ClienteEmpresa.objects.create(nombre='Empresa CD', rut='76.000.001-1')
        cd = CD.objects.create(
            nombre='CD Empresa', codigo='CDE', direccion='Calle 1', comuna='Santiago',
            tipo='cliente', lat=-33.45, lng=-70.65, cliente_empresa=company,
        )
        self.assertEqual(cd.cliente_empresa, company)


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
