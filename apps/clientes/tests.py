from datetime import time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.cds.models import CD
from apps.containers.models import Container

from .models import ClienteEmpresa, ClienteUsuario, SituacionCliente, SolicitudHorario
from .services import ClientSlotRecommendationService


class ClientPortalIsolationTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.company_a = ClienteEmpresa.objects.create(nombre='Cliente A')
        self.company_b = ClienteEmpresa.objects.create(nombre='Cliente B')
        self.user_a = User.objects.create_user('cliente_a', password='***')
        self.user_b = User.objects.create_user('cliente_b', password='***')
        ClienteUsuario.objects.create(user=self.user_a, empresa=self.company_a)
        ClienteUsuario.objects.create(user=self.user_b, empresa=self.company_b)
        self.cd_a = CD.objects.create(
            nombre='CD A', codigo='CDA', direccion='A', comuna='Santiago',
            tipo='cliente', lat=-33.45, lng=-70.65, cliente_empresa=self.company_a,
        )
        self.cd_b = CD.objects.create(
            nombre='CD B', codigo='CDB', direccion='B', comuna='Santiago',
            tipo='cliente', lat=-33.46, lng=-70.66, cliente_empresa=self.company_b,
        )
        self.container_a = Container.objects.create(
            container_id='AAAA1234567', tipo='40', nave='Nave A', estado='liberado',
            cliente_empresa=self.company_a,
        )
        self.container_b = Container.objects.create(
            container_id='BBBB1234567', tipo='40', nave='Nave B', estado='liberado',
            cliente_empresa=self.company_b,
        )

    def test_stock_is_strictly_scoped_to_authenticated_company(self):
        self.client_api.force_authenticate(self.user_a)
        response = self.client_api.get(reverse('cliente_stock'))
        self.assertEqual(response.status_code, 200)
        ids = {row['container_id'] for row in response.data['results']}
        self.assertEqual(ids, {'AAAA1234567'})

    def test_client_cannot_request_another_company_container_or_cd(self):
        self.client_api.force_authenticate(self.user_a)
        start = timezone.now() + timedelta(days=1)
        payload = {
            'container': self.container_b.id, 'cd': self.cd_b.id,
            'inicio': start.isoformat(), 'fin': (start + timedelta(hours=1)).isoformat(),
            'modo': 'manual',
        }
        self.assertEqual(self.client_api.post(reverse('cliente_solicitudes'), payload, format='json').status_code, 400)

    def test_role_landing_exposes_all_four_connected_portals(self):
        response = self.client.get(reverse('role_landing'))
        self.assertContains(response, 'Cliente')
        self.assertContains(response, 'Operaciones')
        self.assertContains(response, 'Control')
        self.assertContains(response, 'Conductor')
        self.assertContains(response, reverse('cliente_login'))
        self.assertContains(response, reverse('driver_login'))

    def test_client_can_submit_request_but_it_does_not_auto_schedule(self):
        self.client_api.force_authenticate(self.user_a)
        start = timezone.now() + timedelta(days=1)
        response = self.client_api.post(reverse('cliente_solicitudes'), {
            'container': self.container_a.id, 'cd': self.cd_a.id,
            'inicio': start.isoformat(), 'fin': (start + timedelta(hours=1)).isoformat(),
            'modo': 'manual',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        request = SolicitudHorario.objects.get(pk=response.data['id'])
        self.assertEqual(request.estado, 'pendiente')
        self.assertFalse(hasattr(self.container_a, 'programacion'))

    def test_client_can_report_situation_and_only_its_own_container(self):
        self.client_api.force_authenticate(self.user_a)
        response = self.client_api.post(reverse('cliente_situaciones'), {
            'container': self.container_a.pk, 'categoria': 'stock',
            'prioridad': 'alta', 'asunto': 'Unidad no visible',
            'mensaje': 'Necesitamos revisión de esta unidad.',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        row = SituacionCliente.objects.get(pk=response.data['id'])
        self.assertEqual(row.empresa, self.company_a)
        self.assertEqual(row.estado, 'abierta')
        denied = self.client_api.post(reverse('cliente_situaciones'), {
            'container': self.container_b.pk, 'categoria': 'stock',
            'asunto': 'No corresponde', 'mensaje': 'Otro tenant',
        }, format='json')
        self.assertEqual(denied.status_code, 400)


class ClientSlotRecommendationTests(TestCase):
    def test_cold_start_is_explicit_and_capacity_is_respected(self):
        company = ClienteEmpresa.objects.create(
            nombre='Cliente Slots', hora_inicio_recepcion=time(8),
            hora_fin_recepcion=time(12), duracion_slot_min=60, capacidad_por_slot=1,
        )
        cd = CD.objects.create(
            nombre='CD Slots', codigo='SLOTS', direccion='A', comuna='Santiago',
            tipo='cliente', lat=-33.45, lng=-70.65, cliente_empresa=company,
        )
        result = ClientSlotRecommendationService.recommend(
            company, cd, (timezone.localdate() + timedelta(days=1)),
        )
        self.assertTrue(result['cold_start'])
        self.assertEqual(len(result['recomendados']), 3)
        self.assertTrue(all(item['fuente'] == 'reglas_capacidad' for item in result['recomendados']))
        self.assertTrue(all(item['cupos_disponibles'] == 1 for item in result['recomendados']))


class OperationsReviewTests(TestCase):
    def test_staff_acceptance_creates_programacion_and_advances_container(self):
        company = ClienteEmpresa.objects.create(nombre='Cliente Review')
        client_user = User.objects.create_user('clientreview', password='***')
        ClienteUsuario.objects.create(user=client_user, empresa=company)
        staff = User.objects.create_user('staffreview', password='***', is_staff=True)
        cd = CD.objects.create(
            nombre='CD Review', codigo='REVIEW', direccion='A', comuna='Santiago',
            tipo='cliente', lat=-33.45, lng=-70.65, cliente_empresa=company,
        )
        container = Container.objects.create(
            container_id='REVU1234567', tipo='40', nave='Nave', estado='liberado',
            cliente_empresa=company,
        )
        start = timezone.now() + timedelta(days=1)
        request = SolicitudHorario.objects.create(
            empresa=company, solicitante=client_user, container=container, cd=cd,
            modo='manual', inicio_solicitado=start, fin_solicitado=start + timedelta(hours=1),
        )
        api = APIClient(); api.force_authenticate(staff)
        response = api.post(reverse('revisar_solicitud_cliente', kwargs={'pk': request.pk}), {
            'decision': 'aceptada', 'respuesta': 'Confirmado',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        container.refresh_from_db(); request.refresh_from_db()
        self.assertEqual(container.estado, 'programado')
        self.assertIsNotNone(request.programacion_id)
        self.assertEqual(request.programacion.container_id, container.id)

    def test_staff_can_answer_client_situation(self):
        company = ClienteEmpresa.objects.create(nombre='Cliente Situation')
        client_user = User.objects.create_user('situation-client', password='***')
        ClienteUsuario.objects.create(user=client_user, empresa=company)
        staff = User.objects.create_user('situation-staff', password='***', is_staff=True)
        row = SituacionCliente.objects.create(
            empresa=company, creada_por=client_user, categoria='operativa',
            prioridad='urgente', asunto='Recepción detenida', mensaje='Favor revisar.',
        )
        api = APIClient(); api.force_authenticate(staff)
        response = api.post(reverse('revisar_situacion_cliente', kwargs={'pk': row.pk}), {
            'estado': 'resuelta', 'respuesta': 'Situación coordinada.',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        row.refresh_from_db()
        self.assertEqual(row.estado, 'resuelta')
        self.assertEqual(row.respuesta_operaciones, 'Situación coordinada.')
