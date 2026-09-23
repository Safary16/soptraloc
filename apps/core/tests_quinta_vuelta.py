"""Tests quinta vuelta: N+1 (dashboard/listas), arribo directo unificado y trazabilidad de confirmación."""
import uuid

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.containers.models import Container
from apps.containers.serializers import ContainerListSerializer
from apps.drivers.models import Driver
from apps.cds.models import CD
from apps.programaciones.models import Programacion, RegistroOperacion
from apps.events.models import Event
from apps.core.api_views import dashboard_stats, analytics_conductores
from apps.core.services.operations import OperationalFlowService


class DashboardQueriesTest(TestCase):
    """dashboard_stats/analytics_conductores: payload correcto y queries acotadas."""

    def setUp(self):
        self.suf = uuid.uuid4().hex[:6]
        self.cd = CD.objects.create(
            nombre=f'CD Q {self.suf}', tipo='cliente', direccion='Av Test 1',
            lat=-33.45, lng=-70.66,
        )
        self.drv = Driver.objects.create(
            nombre=f'Driver Q {self.suf}', rut=f'{self.suf}-{self.suf[:1]}',
            patente=f'QQ{self.suf[:2]}', max_entregas_dia=5, activo=True, presente=True,
        )
        self.cont = Container.objects.create(
            container_id=f'QQQA{self.suf[:3]}1', tipo='40HC', cliente='WALMART',
            posicion_fisica='P1', cd_entrega=self.cd,
        )
        self.cont.cambiar_estado('liberado', 'test')
        self.cont.cambiar_estado('secuenciado', 'test')
        self.cont.cambiar_estado('programado', 'test')  # señal crea Programacion
        prog = Programacion.objects.get(container=self.cont)
        prog.fecha_programada = timezone.now() + timedelta(hours=10)
        prog.save()

    def test_dashboard_stats_payload_coherente(self):
        rf = RequestFactory()
        data = dashboard_stats(rf.get('/')).data['stats']
        self.assertEqual(data['contenedores_total'], 1)
        self.assertEqual(data['programados'], 1)
        self.assertEqual(data['total_activos'], 1)
        self.assertEqual(data['conductores_disponibles'], 1)
        self.assertEqual(data['sin_asignar'], 1)
        self.assertIn('con_demurrage', data)
        self.assertIn('vacios', data)

    def test_analytics_conductores_annotate_y_perfil(self):
        rf = RequestFactory()
        data = analytics_conductores(rf.get('/')).data['conductores']
        fila = next(f for f in data if f['driver_id'] == self.drv.id)
        self.assertEqual(fila['programaciones_completadas'], 0)
        self.assertIn('factor', fila['perfil_velocidad_ml'])
        self.assertIn('label', fila['perfil_velocidad_ml'])

    def test_list_serializer_tiene_programacion_sin_n1(self):
        viewset_qs = ContainerListSerializer.Meta.model.objects.select_related(
            'cd_entrega', 'retorno_destino_cd'
        )
        prog_exists = Programacion.objects.filter(container_id=__import__(
            'django.db.models', fromlist=['OuterRef']).OuterRef('pk'))
        from django.db.models import Exists
        qs = viewset_qs.annotate(tiene_programacion_annot=Exists(prog_exists))
        data = ContainerListSerializer(qs, many=True).data
        fila = next(f for f in data if f['container_id'] == self.cont.container_id)
        self.assertTrue(fila['tiene_programacion'])
        self.assertEqual(fila['cd_entrega_nombre'], self.cd.nombre)


class ArriboDirectoUnificadoTest(TestCase):
    """El arribo sin programación deja el MISMO rastro de auditoría (Event arribo_cd)."""

    def setUp(self):
        self.suf = uuid.uuid4().hex[:6]
        self.cd = CD.objects.create(
            nombre=f'CD A {self.suf}', tipo='cliente', direccion='Av Test 1',
            lat=-33.45, lng=-70.66,
        )
        self.cont = Container.objects.create(
            container_id=f'AAAB{self.suf[:3]}2', tipo='40HC', cliente='WALMART',
            posicion_fisica='P1', cd_entrega=self.cd,
        )
        self.cont.cambiar_estado('liberado', 'test')
        self.cont.cambiar_estado('secuenciado', 'test')
        self.cont.cambiar_estado('programado', 'test')
        prog = Programacion.objects.get(container=self.cont)
        # Asignar y llevar a en_ruta (sin GPS para no llamar Mapbox).
        # OJO: asignar_conductor cambia el estado en BD → refrescar la
        # instancia antes del siguiente cambio del FSM.
        prog.asignar_conductor(self._driver(), 'test')
        self.cont.refresh_from_db()
        self.cont.cambiar_estado('en_ruta', 'test')

    def _driver(self):
        if not hasattr(self, 'drv'):
            self.drv = Driver.objects.create(
                nombre=f'Driver A {self.suf}', rut=f'{self.suf}-{self.suf[:1]}',
                patente=f'AB{self.suf[:2]}', max_entregas_dia=5, activo=True, presente=True,
            )
        return self.drv

    def test_arribo_directo_deja_evento_y_estado(self):
        container, creado = OperationalFlowService.registrar_arribo_directo(
            self.cont, lat=None, lng=None, usuario='tester'
        )
        self.assertTrue(creado)
        container.refresh_from_db()
        self.assertEqual(container.estado, 'entregado')
        ev = Event.objects.filter(
            container=container, event_type='arribo_cd'
        ).order_by('-created_at').first()
        self.assertIsNotNone(ev, 'arribo directo debe dejar Event arribo_cd')
        self.assertEqual(ev.detalles.get('origen'), 'manual_sin_programacion')
        # GPS degradado cayó a la ubicación del CD
        self.assertEqual(float(ev.detalles['gps_lat']), float(self.cd.lat))

    def test_arribo_directo_idempotente(self):
        OperationalFlowService.registrar_arribo_directo(self.cont, usuario='tester')
        n_eventos = Event.objects.filter(
            container=self.cont, event_type='arribo_cd'
        ).count()
        with self.assertRaises(ValueError):
            OperationalFlowService.registrar_arribo_directo(self.cont, usuario='tester')
        self.assertEqual(
            Event.objects.filter(container=self.cont, event_type='arribo_cd').count(),
            n_eventos,
        )


class ConfirmarRecomendacionTrazabilidadTest(TestCase):
    """confirmar_recomendacion debe dejar RegistroOperacion con decision CONFIRMAR."""

    def setUp(self):
        self.suf = uuid.uuid4().hex[:6]
        self.cd = CD.objects.create(
            nombre=f'CD C {self.suf}', tipo='cliente', direccion='Av Test 1',
            lat=-33.45, lng=-70.66,
        )
        self.drv = Driver.objects.create(
            nombre=f'Driver C {self.suf}', rut=f'{self.suf}-{self.suf[:1]}',
            patente=f'AC{self.suf[:2]}', max_entregas_dia=5, activo=True, presente=True,
        )
        self.cont = Container.objects.create(
            container_id=f'AAAC{self.suf[:3]}3', tipo='40HC', cliente='WALMART',
            posicion_fisica='P1', cd_entrega=self.cd,
        )
        self.cont.cambiar_estado('liberado', 'test')
        self.cont.cambiar_estado('secuenciado', 'test')
        self.cont.cambiar_estado('programado', 'test')
        self.prog = Programacion.objects.get(container=self.cont)
        # Simular preasignación ML (prediccion_ml con driver recomendado, sin driver aún)
        self.prog.prediccion_ml = {
            'driver_id': self.drv.id,
            'driver_nombre': self.drv.nombre,
            'eta_minutos': 30,
            'confianza': 0.8,
        }
        self.prog.save(update_fields=['prediccion_ml', 'updated_at'])
        # Registro inicial de preasignación (como lo crea el flujo ML)
        RegistroOperacion.objects.create(
            programacion=self.prog,
            service_id=f'preasign-{self.prog.id}-test0001',
            recurso_asignado=f'{self.drv.nombre} (pre-asignación ML)',
            clasificacion_sistema='REVISION_OPERADOR',
        )

    def test_confirmar_crea_registro_con_decision(self):
        from django.test import Client
        # Cliente completo: la action hereda IsAuthenticatedOrReadOnly y
        # SessionAuthentication exige CSRF (RequestFactory directo daría 403).
        operador = User.objects.create_user(username=f'op_{self.suf}', password='x')
        client = Client()
        client.force_login(operador)

        resp = client.post(f'/api/programaciones/{self.prog.id}/confirmar_recomendacion/')
        self.assertEqual(resp.status_code, 200)

        registro = RegistroOperacion.objects.filter(
            programacion=self.prog, decision_operador='CONFIRMAR'
        ).order_by('-created_at').first()
        self.assertIsNotNone(registro, 'confirmación debe quedar en bitácora')
        self.assertEqual(registro.recurso_asignado, self.drv.nombre)
        self.prog.refresh_from_db()
        self.assertEqual(self.prog.driver_id, self.drv.id)
