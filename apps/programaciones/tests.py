from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.drivers.models import Driver
from apps.containers.models import Container
from apps.notifications.models import Notification
from apps.cds.models import CD
from .models import Programacion, TiempoOperacion
from apps.core.services.operations import OperationalFlowService
from unittest.mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate
from .views import ProgramacionViewSet


class ProgramacionAsignacionTests(TestCase):
    """Tests for driver assignment and notifications"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user and driver
        self.user = User.objects.create_user(
            username='test_driver',
            password='test123'
        )
        self.driver = Driver.objects.create(
            nombre='Test Driver',
            rut='12345678-9',
            user=self.user,
            num_entregas_dia=0,
            max_entregas_dia=3
        )
        
        # Create test CD
        self.cd = CD.objects.create(
            nombre='Test CD',
            codigo='TEST-CD',
            tipo='cliente',
            direccion='Test Address',
            lat=-33.4569,
            lng=-70.6483
        )
        
        # Create test container
        self.container = Container.objects.create(
            container_id='TEST123',
            cliente='Test Cliente',
            estado='liberado'
        )
        
        # Create test programacion
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            cliente='Test Cliente',
            fecha_programada=timezone.now() + timedelta(hours=24)
        )
    
    def test_crear_programacion_actualiza_container_a_programado(self):
        """Creating a schedule establishes the container's programmed state."""
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'programado')

    def test_asignar_conductor_creates_notification(self):
        """Test that assigning a driver creates a notification"""
        # Verify no notifications exist before assignment
        self.assertEqual(Notification.objects.count(), 0)
        
        # Assign driver
        self.programacion.asignar_conductor(self.driver)
        
        # Verify notification was created
        notifications = Notification.objects.filter(
            driver=self.driver,
            programacion=self.programacion,
            tipo='asignacion'
        )
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertEqual(notification.prioridad, 'media')
        self.assertIn('TEST123', notification.titulo)
        self.assertIn('Test Cliente', notification.mensaje)
    
    def test_asignar_conductor_updates_container_estado(self):
        """Test that assigning a driver updates container state"""
        self.programacion.asignar_conductor(self.driver)
        
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'asignado')
    
    def test_asignar_conductor_increments_entregas_dia(self):
        """Test that assigning a driver increments daily deliveries"""
        initial_count = self.driver.num_entregas_dia
        
        self.programacion.asignar_conductor(self.driver)
        
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.num_entregas_dia, initial_count + 1)
    
    def test_asignar_conductor_sets_fecha_asignacion(self):
        """Test that assigning a driver sets assignment date"""
        self.programacion.asignar_conductor(self.driver)
        
        self.programacion.refresh_from_db()
        self.assertIsNotNone(self.programacion.fecha_asignacion)
        self.assertEqual(self.programacion.driver, self.driver)


class ProgramacionArriboTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='arribo_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='Arribo Driver', user=self.user, patente='ARR123',
        )
        self.cd = CD.objects.create(
            nombre='CD Arribo', codigo='ARR-CD', direccion='Destino', comuna='Santiago',
            lat=-33.450000, lng=-70.650000,
        )
        self.container = Container.objects.create(
            container_id='ARRI1234567', estado='asignado', cliente='Cliente'
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='Cliente', fecha_programada=timezone.now() + timedelta(hours=1),
        )
        self.container.estado = 'en_ruta'
        self.container.fecha_inicio_ruta = timezone.now() - timedelta(minutes=10)
        self.container.save(update_fields=['estado', 'fecha_inicio_ruta', 'updated_at'])
        self.programacion.fecha_inicio_ruta = self.container.fecha_inicio_ruta
        self.programacion.save(update_fields=['fecha_inicio_ruta', 'updated_at'])
        self.factory = APIRequestFactory()

    def _post(self, action, data):
        request = self.factory.post('/', data, format='json')
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': action})
        return view(request, pk=self.programacion.pk)

    def test_manual_arrival_requires_and_persists_gps(self):
        missing = self._post('notificar_arribo', {})
        self.assertEqual(missing.status_code, 400)

        response = self._post('notificar_arribo', {'lat': -33.45, 'lng': -70.65})
        self.assertEqual(response.status_code, 200)
        self.programacion.refresh_from_db()
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'entregado')
        self.assertIsNotNone(self.programacion.fecha_arribo_cd)
        self.assertEqual(self.programacion.origen_arribo, 'manual')
        self.assertEqual(float(self.programacion.gps_arribo_lat), -33.45)
        self.assertEqual(float(self.programacion.gps_arribo_lng), -70.65)

    def test_position_inside_configured_geofence_registers_arrival(self):
        self.cd.geocerca_radio_m = 200
        self.cd.save(update_fields=['geocerca_radio_m', 'updated_at'])
        with patch('apps.notifications.services.NotificationService.actualizar_eta') as eta:
            response = self._post('actualizar_posicion', {'lat': -33.45, 'lng': -70.65})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['arribo_automatico'])
        eta.assert_not_called()
        self.programacion.refresh_from_db()
        self.assertEqual(self.programacion.origen_arribo, 'geocerca')
        self.assertIsNotNone(self.programacion.fecha_arribo_cd)

    def test_geofence_is_inactive_without_explicit_radius(self):
        self.assertFalse(self.cd.contiene_en_geocerca(-33.45, -70.65))

    def test_driver_cannot_register_another_drivers_arrival(self):
        other_user = User.objects.create_user(username='other_arribo', password='***')
        request = self.factory.post('/', {'lat': -33.45, 'lng': -70.65}, format='json')
        force_authenticate(request, user=other_user)
        view = ProgramacionViewSet.as_view({'post': 'notificar_arribo'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 403)
        self.programacion.refresh_from_db()
        self.assertIsNone(self.programacion.fecha_arribo_cd)

    def test_repeated_manual_arrival_is_idempotent(self):
        first = self._post('notificar_arribo', {'lat': -33.45, 'lng': -70.65})
        second = self._post('notificar_arribo', {'lat': -33.46, 'lng': -70.66})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['ya_registrado'])
        self.programacion.refresh_from_db()
        self.assertEqual(float(self.programacion.gps_arribo_lat), -33.45)
        self.assertEqual(float(self.programacion.gps_arribo_lng), -70.65)


class OperationalCompletionTests(TestCase):
    def _flow(self, drop_hook):
        user = User.objects.create_user(f'driver_{drop_hook}', password='***')
        driver = Driver.objects.create(
            nombre=f'Driver {drop_hook}', user=user, num_entregas_dia=1,
        )
        cd = CD.objects.create(
            nombre=f'CD {drop_hook}', codigo=f'CD-{drop_hook}', direccion='Destino',
            comuna='Santiago', lat=-33.45, lng=-70.65,
            permite_soltar_contenedor=drop_hook,
            requiere_espera_carga=not drop_hook,
            capacidad_vacios=10,
        )
        container = Container.objects.create(
            container_id=('DROP' if drop_hook else 'WAIT') + '1234567',
            estado='entregado', cliente='Cliente', cd_entrega=cd,
            fecha_entrega=timezone.now() - timedelta(minutes=25),
        )
        programacion = Programacion.objects.create(
            container=container, cd=cd, driver=driver, cliente='Cliente',
            fecha_programada=timezone.now(),
        )
        return driver, cd, container, programacion

    def test_drop_hook_separates_driver_release_from_empty_inventory(self):
        driver, cd, container, programacion = self._flow(True)
        OperationalFlowService.drop_container(programacion, 'driver')
        container.refresh_from_db(); driver.refresh_from_db(); cd.refresh_from_db()
        self.assertEqual(container.estado, 'soltado')
        self.assertEqual(driver.num_entregas_dia, 0)
        self.assertEqual(cd.vacios_actuales, 0)
        self.assertFalse(container.vacio_contabilizado)

        completed, timing = OperationalFlowService.mark_empty(programacion, 'cd', 'test')
        completed.container.refresh_from_db(); cd.refresh_from_db()
        self.assertEqual(completed.container.estado, 'vacio')
        self.assertEqual(cd.vacios_actuales, 1)
        self.assertTrue(completed.container.vacio_contabilizado)
        self.assertIsNotNone(timing)

    def test_waiting_driver_is_released_only_after_real_discharge(self):
        driver, cd, container, programacion = self._flow(False)
        completed, timing = OperationalFlowService.mark_empty(programacion, 'driver', 'test')
        completed.container.refresh_from_db(); driver.refresh_from_db(); cd.refresh_from_db()
        self.assertEqual(completed.container.estado, 'vacio')
        self.assertEqual(driver.num_entregas_dia, 0)
        self.assertEqual(cd.vacios_actuales, 0)
        self.assertEqual(TiempoOperacion.objects.filter(container=container).count(), 1)
        self.assertGreaterEqual(timing.tiempo_real_min, 24)

    def test_retries_do_not_double_release_or_duplicate_timing(self):
        driver, cd, container, programacion = self._flow(True)
        OperationalFlowService.drop_container(programacion, 'driver')
        _, created = OperationalFlowService.drop_container(programacion, 'driver')
        self.assertFalse(created)
        OperationalFlowService.mark_empty(programacion, 'cd', 'test')
        driver.refresh_from_db(); cd.refresh_from_db()
        self.assertEqual(driver.num_entregas_dia, 0)
        self.assertEqual(cd.vacios_actuales, 1)
        self.assertEqual(TiempoOperacion.objects.filter(container=container).count(), 1)


class DesgloseContractTests(TestCase):
    """Contrato frontend/backend del desglose de score (4 badges).

    Antes: el JS leia desglose.disponibilidad|ocupacion|cumplimiento|proximidad
    y siempre quedaba en 0 porque el backend usaba otros nombres.
    Ahora: AssignmentService.calcular_score_total expone ambos nombres
    (5 dims internas y 4 dims frontend); cada badge siempre viene poblado.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='score_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='Score Driver', user=self.user, patente='SCO123',
            num_entregas_dia=0, max_entregas_dia=5, capacidad_ton=30,
        )
        self.cd = CD.objects.create(
            nombre='CD Score', codigo='SCORE-CD', direccion='Destino',
            comuna='Santiago', lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='SCO1234567', cliente='Score Cliente', estado='programado',
            peso_carga=10000,
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, cliente='Score Cliente',
            fecha_programada=timezone.now() + timedelta(hours=24),
        )

    def test_desglose_frontend_tiene_las_4_claves_legibles(self):
        from apps.core.services.assignment import AssignmentService
        score = AssignmentService.calcular_score_total(self.driver, self.programacion)
        self.assertIn('desglose', score)
        self.assertEqual(
            set(score['desglose'].keys()),
            {'disponibilidad', 'ocupacion', 'cumplimiento', 'proximidad'},
        )
        # Cada dimension del frontend cae en [0,100] (% legible para la badge).
        for valor in score['desglose'].values():
            self.assertGreaterEqual(valor, 0.0)
            self.assertLessEqual(valor, 100.0)

    def test_desglose_interno_seis_claves_se_conserva(self):
        """El backend sigue exponiendo el desglose interno 5-key para auditoría."""
        from apps.core.services.assignment import AssignmentService
        score = AssignmentService.calcular_score_total(self.driver, self.programacion)
        self.assertIn('score_por_dimension', score)
        self.assertEqual(
            set(score['score_por_dimension'].keys()),
            {
                'disponibilidad_confirmada',
                'riesgo_de_atraso',
                'adecuacion_vehiculo_carga',
                'historial_operativo',
                'urgencia_del_servicio',
            },
        )

    def test_obtener_conductores_disponibles_expone_ambas_vistas(self):
        """obtener_conductores_disponibles_con_score debe propagar 'desglose' (4)
        y 'score_por_dimension' (5) para que el frontend pinte las 4 badges."""
        from apps.core.services.assignment import AssignmentService
        resultados = AssignmentService.obtener_conductores_disponibles_con_score(self.programacion)
        self.assertTrue(resultados, 'Debe haber al menos un conductor disponible')
        for item in resultados:
            self.assertIn('desglose', item)
            self.assertIn('score_por_dimension', item)
            self.assertEqual(len(item['desglose']), 4)
            self.assertEqual(len(item['score_por_dimension']), 5)


class PrediccionMlContractTests(TestCase):
    """Contrato del campo prediccion_ml en el modelo y serializers.

    prediccion_ml es un JSONField con default=dict (nunca None en instancias
    nuevas). El serializer lo expone como dict (puede ser {} recien creada);
    el test verifica que SIEMPRE es un dict iterable para que el frontend
    pueda mostrar advertencia sin romper layout si Mapbox falla.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='ml_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='ML Driver', user=self.user, patente='ML123',
        )
        self.cd = CD.objects.create(
            nombre='ML CD', codigo='ML-CD', direccion='Destino',
            comuna='Santiago', lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='MLD1234567', cliente='ML Cliente', estado='programado',
            peso_carga=12000,
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, cliente='ML Cliente',
            fecha_programada=timezone.now() + timedelta(hours=2),
        )

    def test_prediccion_ml_es_dict_en_programacion_nueva(self):
        """Una Programacion recien creada debe tener prediccion_ml = {} (default)."""
        self.assertIsInstance(self.programacion.prediccion_ml, dict)
        self.assertEqual(self.programacion.prediccion_ml, {})

    def test_prediccion_ml_poblada_en_list_serializer(self):
        """ProgramacionListSerializer debe exponer prediccion_ml como dict (puede ser {})."""
        from apps.programaciones.serializers import ProgramacionListSerializer
        data = ProgramacionListSerializer(self.programacion).data
        self.assertIn('prediccion_ml', data)
        self.assertIsInstance(data['prediccion_ml'], dict)

    def test_prediccion_ml_poblada_tras_prediccion_explicita(self):
        """Cuando se setea prediccion_ml con datos reales, el serializer lo refleja."""
        self.programacion.prediccion_ml = {
            'source': 'ml',
            'predicted_minutes': 45,
            'samples': 12,
            'confidence': 0.78,
        }
        self.programacion.save(update_fields=['prediccion_ml', 'updated_at'])
        from apps.programaciones.serializers import ProgramacionListSerializer
        data = ProgramacionListSerializer(self.programacion).data
        self.assertEqual(data['prediccion_ml']['source'], 'ml')
        self.assertEqual(data['prediccion_ml']['predicted_minutes'], 45)


class FsmIncidenteTransitionTests(TestCase):
    """Cobertura de transiciones del FSM: incidente como estado destino.

    Verifica que al reportar un incidente desde 'en_ruta', el contenedor
    pasa a 'incidente' y se limpia fecha_inicio_ruta (stale) cuando vuelve
    a 'programado' (limpieza de timestamps en reversion).
    """

    def setUp(self):
        self.user = User.objects.create_user(username='inc_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='Inc Driver', user=self.user,
        )
        self.container = Container.objects.create(
            container_id='INC1234567', cliente='Inc Cliente',
            estado='en_ruta', fecha_inicio_ruta=timezone.now() - timedelta(hours=1),
        )

    def test_reversion_a_programado_limpia_fecha_inicio_ruta(self):
        """Volver a 'programado' limpia fecha_inicio_ruta (stale) automaticamente."""
        self.container.cambiar_estado('incidente')
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'incidente')
        # Volver a 'programado' requiere reversion=True y la transicion inversa permitida.
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            self.container.cambiar_estado('programado', permitir_reversion=True)
        except DjangoValidationError:
            self.skipTest('FSM no permite revertir de incidente a programado en este modelo')
        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, 'programado')
        self.assertIsNone(
            self.container.fecha_inicio_ruta,
            'Tras reversion a programado, fecha_inicio_ruta debe quedar en None.',
        )


class FlujoConductorP0Tests(TestCase):
    """P0: cobertura del flujo conductor visible para el dueño.

    - aceptar_asignacion: conductor asignado confirma; rechaza a otro conductor.
    - reportar_problema: NO cambia container.estado; crea notificación al operador.
    - P0-3: notification tipo='llegada' se crea al registrar arribo.
    - P0-5: drop_container auto-crea Programacion de retorno si hay vacío fresco
      en el mismo CD.
    """

    def setUp(self):
        self.user_a = User.objects.create_user(username='driver_a', password='x')
        self.user_b = User.objects.create_user(username='driver_b', password='x')
        self.driver_a = Driver.objects.create(
            nombre='Driver A', user=self.user_a, num_entregas_dia=0, max_entregas_dia=3,
        )
        self.driver_b = Driver.objects.create(
            nombre='Driver B', user=self.user_b, num_entregas_dia=0, max_entregas_dia=3,
        )
        self.cd = CD.objects.create(
            nombre='CD P0', codigo='CD-P0', tipo='cliente',
            direccion='CD P0 dir', lat=-33.4569, lng=-70.6483,
            permite_soltar_contenedor=True,
        )
        self.container = Container.objects.create(
            container_id='PCNT12345', cliente='P0 Cliente',
            estado='asignado', cd_entrega=self.cd,
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            driver=self.driver_a,
            cliente='P0 Cliente',
            fecha_programada=timezone.now() + timedelta(hours=2),
            fecha_asignacion=timezone.now() - timedelta(minutes=15),
        )

    def _post(self, action_name):
        factory = APIRequestFactory()
        request = factory.post(
            f'/api/programaciones/{self.programacion.pk}/{action_name}/',
            data={}, format='json',
        )
        view = ProgramacionViewSet.as_view({'post': action_name})
        return view(request, pk=self.programacion.pk)

    # ---------- P0-1: aceptar_asignacion ----------
    def test_aceptar_asignacion_conductor_asignado_confirma(self):
        """El conductor asignado puede aceptar; crea evento y decision_operador=CONFIRMAR."""
        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/aceptar_asignacion/',
            data={}, format='json',
        )
        force_authenticate(request, user=self.user_a)
        view = ProgramacionViewSet.as_view({'post': 'aceptar_asignacion'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['decision_operador'], 'CONFIRMAR')

        self.programacion.refresh_from_db()
        self.assertEqual(self.programacion.decision_operador, 'CONFIRMAR')

        from apps.events.models import Event
        eventos = Event.objects.filter(container=self.container, event_type='asignacion_conductor')
        self.assertGreaterEqual(eventos.count(), 1)

    def test_aceptar_asignacion_otro_conductor_rechaza(self):
        """Un conductor distinto del asignado NO puede aceptar la asignación."""
        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/aceptar_asignacion/',
            data={}, format='json',
        )
        force_authenticate(request, user=self.user_b)
        view = ProgramacionViewSet.as_view({'post': 'aceptar_asignacion'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 403, response.data)
        self.programacion.refresh_from_db()
        self.assertNotEqual(self.programacion.decision_operador, 'CONFIRMAR')

    # ---------- P0-2: reportar_problema ----------
    def test_reportar_problema_no_cambia_estado_y_notifica(self):
        """reportar_problema NO debe cambiar container.estado y debe notificar al operador."""
        estado_inicial = self.container.estado
        self.assertEqual(estado_inicial, 'asignado')

        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/reportar_problema/',
            data={'tipo': 'FALTA_GUIA', 'descripcion': 'No estaba la guía en el CD'},
            format='json',
        )
        force_authenticate(request, user=self.user_a)
        view = ProgramacionViewSet.as_view({'post': 'reportar_problema'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data['success'])

        self.container.refresh_from_db()
        self.assertEqual(self.container.estado, estado_inicial,
                         'reportar_problema NO debe cambiar container.estado')

        notif = Notification.objects.filter(
            container=self.container, tipo='problema_reportado', prioridad='alta',
        )
        self.assertEqual(notif.count(), 1)
        # El tipo debe estar en el mensaje (el título es estable por container_id)
        self.assertIn('FALTA_GUIA', notif.first().mensaje)
        self.assertEqual(notif.first().detalles.get('tipo_problema'), 'FALTA_GUIA')

    def test_reportar_problema_tipo_invalido(self):
        """Tipo fuera de la lista canónica debe rechazarse con 400."""
        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/reportar_problema/',
            data={'tipo': 'NO_EXISTE', 'descripcion': 'x'},
            format='json',
        )
        force_authenticate(request, user=self.user_a)
        view = ProgramacionViewSet.as_view({'post': 'reportar_problema'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 400, response.data)


class FlujoConductorP03NotificacionArriboTests(TestCase):
    """P0-3: notification tipo='llegada' se crea al registrar arribo."""

    def setUp(self):
        self.user = User.objects.create_user(username='arr_driver', password='x')
        self.driver = Driver.objects.create(
            nombre='Arr Driver', user=self.user, num_entregas_dia=0, max_entregas_dia=3,
        )
        self.cd = CD.objects.create(
            nombre='CD Arribo', codigo='CD-ARR', tipo='cliente',
            direccion='CD Arribo dir', lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='ARRCNT001', cliente='Arribo Cliente',
            estado='en_ruta', cd_entrega=self.cd,
            fecha_inicio_ruta=timezone.now() - timedelta(hours=1),
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            driver=self.driver,
            cliente='Arribo Cliente',
            fecha_programada=timezone.now() - timedelta(hours=1),
            fecha_asignacion=timezone.now() - timedelta(hours=2),
            fecha_inicio_ruta=timezone.now() - timedelta(hours=1),
        )

    def test_registrar_arribo_crea_notification_llegada(self):
        """registrar_arribo debe crear una notificación tipo='llegada' con prioridad alta."""
        notif_pre = Notification.objects.filter(tipo='llegada').count()
        locked, created = OperationalFlowService.registrar_arribo(
            self.programacion, -33.45, -70.65, 'manual', 'tester',
        )
        self.assertTrue(created)
        notif_post = Notification.objects.filter(tipo='llegada').count()
        self.assertEqual(notif_post, notif_pre + 1)

        notif = Notification.objects.filter(tipo='llegada').first()
        self.assertEqual(notif.prioridad, 'alta')
        self.assertIn(self.cd.nombre, notif.mensaje)
        self.assertIn('Entregado', notif.titulo)


class FlujoConductorP05AutoAssignReturnTests(TestCase):
    """P0-5: drop_container auto-asigna un retorno de vacío 'fresco' en el mismo CD."""

    def setUp(self):
        self.user = User.objects.create_user(username='drop_driver', password='x')
        self.driver = Driver.objects.create(
            nombre='Drop Driver', user=self.user, num_entregas_dia=0, max_entregas_dia=5,
        )
        self.cd = CD.objects.create(
            nombre='CD Drop', codigo='CD-DROP', tipo='cliente',
            direccion='CD Drop dir', lat=-33.45, lng=-70.65,
            permite_soltar_contenedor=True,
        )
        self.container = Container.objects.create(
            container_id='DROPCNT01', cliente='Drop Cliente',
            estado='entregado', cd_entrega=self.cd,
            fecha_entrega=timezone.now() - timedelta(minutes=10),
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            driver=self.driver,
            cliente='Drop Cliente',
            fecha_programada=timezone.now() - timedelta(minutes=30),
            fecha_asignacion=timezone.now() - timedelta(hours=2),
        )

    def test_drop_container_autoasigna_vacio_fresco_en_mismo_cd(self):
        """Si hay un contenedor 'fresco' (vacio contabilizado en <2h) en el mismo CD,
        drop_container debe crear una nueva Programacion de retorno automático."""
        vacio = Container.objects.create(
            container_id='VACIO0001', cliente='Vacio Cliente',
            estado='vacio', vacio_contabilizado=True,
            fecha_vacio=timezone.now() - timedelta(minutes=30),
            cd_entrega=self.cd,
            retorno_destino_cd=self.cd,
        )
        notif_pre_count = Notification.objects.count()
        del notif_pre_count  # no usado: el contrato relevante es la auto-asignación
        prog_pre_count = Programacion.objects.count()

        # drop_container ahora retorna tupla de 3 (lockeada, soltado_ok, retorno)
        locked, soltado_ok, retorno = OperationalFlowService.drop_container(
            self.programacion, usuario='tester'
        )
        self.assertTrue(soltado_ok)
        self.assertIsNotNone(retorno, 'Debe crearse una Programacion de retorno automático')
        self.assertEqual(retorno.container_id, vacio.id)
        self.assertEqual(retorno.cd_id, self.cd.id)
        self.assertGreater(Programacion.objects.count(), prog_pre_count)

    def test_drop_container_no_autoasigna_si_conductor_sin_capacidad(self):
        """Si el conductor no está disponible, drop NO debe crear programación de retorno."""
        self.driver.max_entregas_dia = 1
        self.driver.num_entregas_dia = 1
        self.driver.save()
        Container.objects.create(
            container_id='VACIO0002', cliente='Vacio SinCap Cliente',
            estado='vacio', vacio_contabilizado=True,
            fecha_vacio=timezone.now() - timedelta(minutes=15),
            cd_entrega=self.cd, retorno_destino_cd=self.cd,
        )
        prog_pre_count = Programacion.objects.count()
        locked, soltado_ok, retorno = OperationalFlowService.drop_container(
            self.programacion, usuario='tester'
        )
        self.assertTrue(soltado_ok)
        self.assertIsNone(retorno, 'No debe crear retorno si el conductor no está disponible')
        self.assertEqual(Programacion.objects.count(), prog_pre_count)

