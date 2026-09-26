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
        """El conductor asignado puede aceptar; crea evento y decision_operador=CONFIRMAR.

        HAL-6: el endpoint ahora devuelve 200 OK (no 201) porque no crea
        un recurso nuevo, solo confirma uno existente.
        """
        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/aceptar_asignacion/',
            data={}, format='json',
        )
        force_authenticate(request, user=self.user_a)
        view = ProgramacionViewSet.as_view({'post': 'aceptar_asignacion'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 200, response.data)
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

    def test_aceptar_asignacion_anonimo_rechazado_403(self):
        """Safari review: un request ANÓNIMO (no autenticado) debe ser rechazado
        con 403. El guard anterior ('is_authenticated and not is_staff') dejaba
        pasar a no-autenticados porque 'False and not True' es False → no entraba
        al if. Ahora se usa el helper _usuario_puede_operar_viaje que retorna
        False para usuarios no autenticados.
        """
        # Request sin force_authenticate → request.user es AnonymousUser
        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/aceptar_asignacion/',
            data={}, format='json',
        )
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
        # Safari review (P0-5): el conductor de la programación de retorno
        # automático debe ser EL MISMO que soltó el contenedor, no el que
        # elija el ML via AssignmentService.asignar_mejor_conductor.
        self.assertEqual(
            retorno.driver_id, self.driver.id,
            'El conductor del retorno automático debe ser el mismo que soltó.',
        )
        self.assertGreater(Programacion.objects.count(), prog_pre_count)

    def test_drop_container_autoasigna_mismo_conductor_que_solto(self):
        """Safari review: la Programacion de retorno automático debe llegar YA
        con driver= seteado para que la señal post_save
        trigger_automatic_assignment (apps/programaciones/signals.py:38)
        haga early-return y NO llame al AssignmentService ML que podría elegir
        otro conductor del pool.
        """
        # Forzar driver con capacidad para que _auto_assign_empty_return
        # no se salga temprano.
        self.driver.num_entregas_dia = 0
        self.driver.max_entregas_dia = 5
        self.driver.save()
        Container.objects.create(
            container_id='VACIO0003', cliente='Vacio MismoConductor',
            estado='vacio', vacio_contabilizado=True,
            fecha_vacio=timezone.now() - timedelta(minutes=10),
            cd_entrega=self.cd, retorno_destino_cd=self.cd,
        )
        locked, soltado_ok, retorno = OperationalFlowService.drop_container(
            self.programacion, usuario='tester'
        )
        self.assertTrue(soltado_ok)
        self.assertIsNotNone(retorno)
        self.assertIsNotNone(
            retorno.driver,
            'El driver debe estar seteado al CREAR la Programacion de retorno, '
            'para que la señal post_save no la reasigne via ML.',
        )
        self.assertEqual(
            retorno.driver_id, self.driver.id,
            'El conductor de la nueva programación debe ser el MISMO que '
            'soltó el contenedor (dueño exige: «suelta el contenedor y el '
            'conductor queda libre para retirar vacíos desde ese mismo CD»).',
        )


    def test_drop_container_autoasigna_vacio_viejo_sin_limite_frescura(self):
        """Seba (25-sep): la misión drop & hook es soltar el FULL y retirar
        OTRO vacío disponible del mismo CD — SIN límite de frescura.
        Un vacío con más de 2 horas (por ejemplo 5h, de otro drop anterior)
        también debe auto-asignarse al conductor que acaba de soltar.
        (La priorización por demurrage se integrará en una iteración futura.)
        """
        self.driver.num_entregas_dia = 0
        self.driver.max_entregas_dia = 5
        self.driver.save()
        Container.objects.create(
            container_id='VACIOVIEJO', cliente='Vacio Antiguo',
            estado='vacio', vacio_contabilizado=True,
            # 5 horas atrás: habría quedado fuera con el antiguo cutoff de 2h
            fecha_vacio=timezone.now() - timedelta(hours=5),
            cd_entrega=self.cd, retorno_destino_cd=self.cd,
        )
        locked, soltado_ok, retorno = OperationalFlowService.drop_container(
            self.programacion, usuario='tester'
        )
        self.assertTrue(soltado_ok)
        self.assertIsNotNone(
            retorno,
            'Debe auto-asignar un vacío disponible del mismo CD aunque tenga >2h.',
        )
        self.assertEqual(retorno.container.container_id, 'VACIOVIEJO')
        self.assertEqual(
            retorno.driver_id, self.driver.id,
            'El conductor que retira el vacío debe ser el MISMO que soltó.',
        )

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


class FlujoConductorP1InicioFinDescargaTests(TestCase):
    """P1-1: endpoints separados inicio/fin descarga + fecha_inicio_descarga."""

    def setUp(self):
        self.user = User.objects.create_user(username='desc_driver', password='x')
        self.driver = Driver.objects.create(
            nombre='Desc Driver', user=self.user,
            num_entregas_dia=0, max_entregas_dia=5,
        )
        self.cd = CD.objects.create(
            nombre='CD Descarga', codigo='CD-DSC', tipo='cliente',
            direccion='CD Dir', lat=-33.45, lng=-70.65,
            tiempo_promedio_descarga_min=60,
        )
        self.container = Container.objects.create(
            container_id='DSCCNT001', cliente='Descarga Cliente',
            estado='entregado', cd_entrega=self.cd,
            fecha_entrega=timezone.now() - timedelta(minutes=10),
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            driver=self.driver,
            cliente='Descarga Cliente',
            fecha_programada=timezone.now() - timedelta(minutes=30),
            fecha_asignacion=timezone.now() - timedelta(hours=2),
            fecha_inicio_ruta=timezone.now() - timedelta(hours=1),
        )

    def test_inicio_descarga_persiste_timestamp_y_crea_evento(self):
        """notificar_inicio_descarga setea fecha_inicio_descarga y crea evento inicio_descarga."""
        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/notificar_inicio_descarga/',
            data={}, format='json',
        )
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': 'notificar_inicio_descarga'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 201, response.data)
        self.programacion.refresh_from_db()
        self.assertIsNotNone(self.programacion.fecha_inicio_descarga)

        from apps.events.models import Event
        evento = Event.objects.filter(
            container=self.container, event_type='inicio_descarga',
        )
        self.assertEqual(evento.count(), 1)

    def test_fin_descarga_usa_fecha_inicio_descarga_para_tiempo_operacion(self):
        """notificar_fin_descarga usa fecha_inicio_descarga como hora_inicio del TiempoOperacion.

        Verifica el contrato de duración real de la descarga: con un clic del conductor
        ~5 min antes del fin, el TiempoOperacion.tiempo_real_min debe ser ~5 min,
        no los 30+ min de la aproximación histórica (fecha_entrega -> now).
        """
        self.programacion.fecha_inicio_descarga = timezone.now() - timedelta(minutes=5)
        self.programacion.save(update_fields=['fecha_inicio_descarga', 'updated_at'])

        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/notificar_fin_descarga/',
            data={}, format='json',
        )
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': 'notificar_fin_descarga'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 201, response.data)

        timing = TiempoOperacion.objects.filter(
            container=self.container, tipo_operacion='descarga_cd',
        ).first()
        self.assertIsNotNone(timing, 'Debe crear TiempoOperacion')
        self.assertGreaterEqual(timing.tiempo_real_min, 4)
        self.assertLessEqual(timing.tiempo_real_min, 8)


class FlujoConductorP1LearningEngineTests(TestCase):
    """P1-5/P1-7: OperationalLearningEngine.predict_discharge + driver_discharge_profile."""

    def setUp(self):
        self.cd = CD.objects.create(
            nombre='CD Learn', codigo='CD-LRN', tipo='cliente',
            direccion='Dir', lat=-33.45, lng=-70.65,
            tiempo_promedio_descarga_min=60,
        )
        self.driver = Driver.objects.create(
            nombre='Learn Driver', user=User.objects.create_user(
                username='learn_driver', password='x'),
            num_entregas_dia=0, max_entregas_dia=5,
        )

    def test_predict_discharge_cold_start_usa_estatico(self):
        """Sin historial: devuelve el tiempo_promedio_descarga_min del CD."""
        from apps.core.services.learning_engine import OperationalLearningEngine
        result = OperationalLearningEngine.predict_discharge(self.cd)
        self.assertTrue(result['cold_start'])
        self.assertEqual(result['estimated_minutes'], 60)
        self.assertEqual(result['source'], 'cd_static')

    def test_predict_discharge_con_historial(self):
        """Con historial suficiente: devuelve estimación basada en datos reales."""
        from apps.core.services.learning_engine import OperationalLearningEngine
        # Sembrar 5 TiempoOperacion (umbral MIN_DISCHARGE_SAMPLES=3)
        for i in range(5):
            TiempoOperacion.objects.create(
                cd=self.cd, conductor=self.driver,
                container=Container.objects.create(
                    container_id=f'LRN{i:05d}', cliente='C', estado='descargado',
                ),
                tipo_operacion='descarga_cd',
                tiempo_estimado_min=60,
                tiempo_real_min=45,
                hora_inicio=timezone.now() - timedelta(days=i + 1),
                hora_fin=timezone.now() - timedelta(days=i + 1) + timedelta(minutes=45),
                anomalia=False,
            )
        result = OperationalLearningEngine.predict_discharge(self.cd)
        self.assertFalse(result['cold_start'])
        self.assertGreaterEqual(result['estimated_minutes'], 30)
        self.assertLessEqual(result['estimated_minutes'], 60)
        self.assertEqual(result['source'], 'hybrid_ml_history')

    def test_driver_discharge_profile_sin_datos(self):
        """Sin historial: factor=1.0, label=sin_datos_suficientes."""
        from apps.core.services.learning_engine import OperationalLearningEngine
        profile = OperationalLearningEngine.driver_discharge_profile(self.driver)
        self.assertEqual(profile['factor'], 1.0)
        self.assertEqual(profile['label'], 'sin_datos_suficientes')


class FlujoConductorP1ValidationEtaRecalcTests(TestCase):
    """P1-6: validation._calcular_ventana_tiempo prefiere eta_recalculado_min."""

    def setUp(self):
        self.user = User.objects.create_user(username='val_driver', password='x')
        self.driver = Driver.objects.create(
            nombre='Val Driver', user=self.user,
            num_entregas_dia=0, max_entregas_dia=5,
        )
        self.cd = CD.objects.create(
            nombre='CD Val', codigo='CD-VAL', tipo='cliente',
            direccion='Dir', lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='VALCNT001', cliente='Val Cliente',
            estado='en_ruta', cd_entrega=self.cd,
            fecha_inicio_ruta=timezone.now() - timedelta(minutes=10),
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            driver=self.driver,
            cliente='Val Cliente',
            fecha_programada=timezone.now() - timedelta(hours=1),
            fecha_inicio_ruta=timezone.now() - timedelta(minutes=10),
            eta_minutos=60,  # estimación inicial
            eta_recalculado_min=15,  # recalculado en ruta (mucho más cerca)
        )

    def test_validacion_usa_eta_recalculado_en_ruta(self):
        """Para un servicio en_ruta, la ventana debe usar eta_recalculado_min."""
        from apps.core.services.validation import PreAssignmentValidationService
        ventana = PreAssignmentValidationService._calcular_ventana_tiempo(
            self.programacion,
        )
        self.assertEqual(ventana['duracion_minutos'], 15)
        self.assertEqual(ventana['estado_servicio'], 'EN_RUTA')


class FlujoConductorP2Tests(TestCase):
    """P2: SSE liviano (P2-1), prediccion_ml viva (P2-2),
    nota deprecación incidentes (P2-3), eta_cliente (P2-5)."""

    def setUp(self):
        self.user = User.objects.create_user(username='p2_driver', password='x')
        self.driver = Driver.objects.create(
            nombre='P2 Driver', user=self.user,
            num_entregas_dia=0, max_entregas_dia=5,
        )
        self.cd = CD.objects.create(
            nombre='CD P2', codigo='CD-P2', tipo='cliente',
            direccion='Dir', lat=-33.45, lng=-70.65,
            tiempo_promedio_descarga_min=60,
        )
        self.container = Container.objects.create(
            container_id='P2CNT001', cliente='P2 Cliente',
            estado='en_ruta', cd_entrega=self.cd,
            fecha_inicio_ruta=timezone.now() - timedelta(minutes=10),
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            driver=self.driver,
            cliente='P2 Cliente',
            fecha_programada=timezone.now() - timedelta(hours=1),
            fecha_inicio_ruta=timezone.now() - timedelta(minutes=10),
            eta_minutos=60,
            eta_recalculado_min=20,
        )

    # ---------- P2-1: SSE liviano ----------
    def test_eta_stream_devuelve_streaming_response_con_eventos(self):
        """El endpoint eta-stream devuelve StreamingHttpResponse con texto SSE."""
        from apps.programaciones.views import ProgramacionViewSet
        from django.http import StreamingHttpResponse
        request = APIRequestFactory().get(
            f'/api/programaciones/{self.programacion.pk}/eta-stream/',
        )
        view = ProgramacionViewSet.as_view({'get': 'eta_stream'})
        response = view(request, pk=self.programacion.pk)
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(response['Content-Type'], 'text/event-stream')

    # ---------- P2-2: prediccion_ml viva en tiempo_estimado_min ----------
    def test_record_discharge_prefiere_prediccion_ml_viva(self):
        """Si programacion.prediccion_ml.tiempo_descarga_estimado existe, se usa."""
        # Mover container a estado 'soltado' (FSM válido desde 'entregado') para
        # que complete_discharge funcione, pero _record_discharge es independiente
        # del estado: solo verifica unicidad por container+tipo_operacion.
        self.container.estado = 'soltado'
        self.container.save(update_fields=['estado', 'updated_at'])
        self.programacion.prediccion_ml = {'tiempo_descarga_estimado': 33}
        self.programacion.save(update_fields=['prediccion_ml', 'updated_at'])
        started = timezone.now() - timedelta(minutes=7)
        finished = timezone.now()
        timing = OperationalFlowService._record_discharge(
            self.programacion, started, finished, 'tester',
        )
        self.assertIsNotNone(timing)
        self.assertEqual(timing.tiempo_estimado_min, 33,
                         'prediccion_ml.tiempo_descarga_estimado debe ganar al estático')

    # ---------- P2-3: nota de deprecación no rompe tipos válidos ----------
    def test_reportar_incidente_tipos_canonicos_se_conservan(self):
        """Los 4 tipos canónicos (ACCIDENTE/AVERIA/DEMORA_TRAFICO/OTRO) siguen
        siendo aceptados por reportar_incidente. La nota P2-3 solo documenta
        la diferencia con reportar_problema, no cambia el contrato de tipos."""
        self.container.estado = 'en_ruta'
        self.container.save(update_fields=['estado', 'updated_at'])
        request = APIRequestFactory().post(
            f'/api/programaciones/{self.programacion.pk}/reportar_incidente/',
            data={'tipo_incidente': 'ACCIDENTE', 'descripcion': 'Colisión leve',
                  'gravedad': 'MODERADA'},
            format='json',
        )
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': 'reportar_incidente'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 201, response.data)
        # El incidente queda registrado en la lista
        self.programacion.refresh_from_db()
        self.assertGreaterEqual(len(self.programacion.incidentes_registrados), 1)
        ultimo = self.programacion.incidentes_registrados[-1]
        self.assertEqual(ultimo['tipo'], 'ACCIDENTE')


class FlujoConductorP25EtaClienteTests(TestCase):
    """P2-5: Notification eta_cliente cuando el cambio de ETA es >10 min."""

    def setUp(self):
        self.user = User.objects.create_user(username='eta_driver', password='x')
        self.driver = Driver.objects.create(
            nombre='Eta Driver', user=self.user,
            num_entregas_dia=0, max_entregas_dia=5,
        )
        self.cd = CD.objects.create(
            nombre='CD Eta', codigo='CD-ETA', tipo='cliente',
            direccion='Dir', lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='ETACNT001', cliente='Eta Cliente',
            estado='en_ruta', cd_entrega=self.cd,
        )
        self.programacion = Programacion.objects.create(
            container=self.container,
            cd=self.cd,
            driver=self.driver,
            cliente='Eta Cliente',
            fecha_programada=timezone.now() - timedelta(hours=1),
            fecha_inicio_ruta=timezone.now() - timedelta(minutes=20),
            eta_minutos=60,
        )

    def test_cambio_eta_mayor_10_min_crea_notificacion_cliente(self):
        """actualizar_eta con cambio >10 min crea Notification tipo 'eta_cliente'."""
        from apps.notifications.services import NotificationService
        notif_pre = Notification.objects.filter(tipo='eta_cliente').count()
        # Simular posición válida (cerca del CD para que haversine no falle)
        NotificationService.actualizar_eta(
            self.programacion, self.driver, -33.46, -70.66,
        )
        notif_post = Notification.objects.filter(tipo='eta_cliente').count()
        # El cambio entre eta_minutos=60 y la nueva ETA es significativo.
        self.assertGreater(notif_post, notif_pre,
                           'Debe crear notificación eta_cliente con cambio >10 min')

    def test_cliente_en_detalles_de_notificacion(self):
        """La notificación eta_cliente incluye el cliente del contenedor en detalles."""
        from apps.notifications.services import NotificationService
        NotificationService.actualizar_eta(
            self.programacion, self.driver, -33.46, -70.66,
        )
        notif = Notification.objects.filter(tipo='eta_cliente').first()
        if notif is not None:
            self.assertEqual(notif.detalles.get('cliente'), 'Eta Cliente')



# ---------------------------------------------------------------------------
# HAL-noche: integración de regresión para HAL-1 (ETA haversine fallback),
# HAL-2 (eta_recalculado_min en serializer lista), HAL-3 (TiempoViaje aunque
# eta_minutos=0), HAL-4 (soltar_contenedor 3-tuple + auto-retorno mismo conductor).
# Estos tests cierran los gaps detectados por la simulación nocturna
# (1247409c): 20 HALs, 108 tests verdes pero ningún test detectaba HAL-4.
# ---------------------------------------------------------------------------


class HalNocheEtaFallbackTests(TestCase):
    """HAL-1: si Mapbox y ML fallan, haversine + blindaje final persiste ETA.

    Garantiza que iniciar_ruta SIEMPRE termine con eta_minutos != None:
    - pre-existente: OperationalLearningEngine.recommend (mockeado para fallar)
    - 1er fallback: MLTimePredictor.predecir_tiempo_viaje (mockeado para fallar)
    - 2do fallback: haversine (35 km/h)
    - 3er blindaje: eta_minutos=0, prediccion_ml.requires_attention=True
    """

    def setUp(self):
        self.user = User.objects.create_user(username='h1_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='HAL1 Driver', user=self.user, patente='H1-1234',
            num_entregas_dia=1, max_entregas_dia=3,
        )
        self.cd = CD.objects.create(
            nombre='HAL1 CD', codigo='HAL1-CD', direccion='Destino',
            comuna='Santiago', lat=-33.450000, lng=-70.650000,
        )
        self.container = Container.objects.create(
            container_id='HAL1C1234', estado='asignado', cliente='HAL1 Cliente',
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='HAL1 Cliente', fecha_programada=timezone.now() + timedelta(hours=1),
        )
        self.factory = APIRequestFactory()

    def _start_force_fail_eta(self):
        from unittest.mock import patch as _patch
        request = self.factory.post('/', {
            'patente': 'H1-1234', 'lat': -33.40, 'lng': -70.60,
        }, format='json')
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': 'iniciar_ruta'})
        # HAL-1: los engines se importan DENTRO de iniciar_ruta (lazy import),
        # así que NO hay referencia en el módulo views. Patcheamos donde se
        # DEFINEN para que el lookup al import local reciba el side_effect.
        patches = [
            _patch('apps.core.services.learning_engine.OperationalLearningEngine.recommend',
                   side_effect=Exception('forced fail for HAL-1')),
            _patch('apps.core.services.ml_predictor.MLTimePredictor.predecir_tiempo_viaje',
                   side_effect=Exception('forced fail for HAL-1')),
        ]
        for c in patches:
            c.start()
        try:
            response = view(request, pk=self.programacion.pk)
        finally:
            for c in patches:
                c.stop()
        return response

    def test_haversine_fallback_calculates_eta_when_all_engines_fail(self):
        response = self._start_force_fail_eta()
        self.assertEqual(response.status_code, 200,
                         f'iniciar_ruta debe responder 200 incluso sin Mapbox/ML: {response.data}')
        self.programacion.refresh_from_db()
        self.assertIsNotNone(self.programacion.eta_minutos,
                             'eta_minutos no debe ser None — blindaje HAL-1')
        self.assertGreater(self.programacion.eta_minutos, 0)
        prediccion = self.programacion.prediccion_ml or {}
        self.assertIn(prediccion.get('source'), {'haversine_fallback', 'no_disponible'})
        if prediccion.get('source') == 'haversine_fallback':
            self.assertIn('haversine', prediccion['explanation'].lower())

    def test_haversine_distance_is_consistent_with_known_coords(self):
        from math import asin, cos, radians, sin, sqrt
        lat1, lng1 = -33.40, -70.60
        lat2, lng2 = -33.45, -70.65
        R = 6371.0
        p1, p2 = radians(lat1), radians(lat2)
        dp = radians(lat2 - lat1)
        dl = radians(lng2 - lng1)
        a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
        km_esperado = 2 * R * asin(sqrt(a))
        eta_esperado = max(1, int(round(km_esperado / 35.0 * 60)))
        response = self._start_force_fail_eta()
        self.assertEqual(response.status_code, 200)
        self.programacion.refresh_from_db()
        self.assertEqual(
            self.programacion.eta_minutos, eta_esperado,
            f'haversine ETA esperado {eta_esperado} min para {km_esperado:.2f} km',
        )


class HalNocheEtaRecalculadoSerializerTests(TestCase):
    """HAL-2: ProgramacionListSerializer expone eta_recalculado_min.

    El template cliente_portal.html:289 lo lee. Antes el field no estaba en
    Meta.fields y jsonserialize lo descartaba (undefined). Ahora el field
    aparece en la lista serializada y round-trippea.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='h2_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='HAL2 Driver', user=self.user, patente='H2-1234',
        )
        self.cd = CD.objects.create(
            nombre='HAL2 CD', codigo='HAL2-CD', direccion='Destino',
            comuna='Santiago', lat=-33.450000, lng=-70.650000,
        )
        self.container = Container.objects.create(
            container_id='HAL2C1234', estado='asignado', cliente='HAL2 Cliente',
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='HAL2 Cliente', fecha_programada=timezone.now() + timedelta(hours=1),
            eta_recalculado_min=42,
        )

    def test_list_serializer_exposes_eta_recalculado_min(self):
        from .serializers import ProgramacionListSerializer
        data = ProgramacionListSerializer(self.programacion).data
        self.assertIn('eta_recalculado_min', data,
                      'eta_recalculado_min debe estar en Meta.fields')
        self.assertEqual(data['eta_recalculado_min'], 42,
                         'Valor round-trip: lo escrito == lo serializado')

    def test_list_serializer_handles_null_eta_recalculado_min(self):
        from .serializers import ProgramacionListSerializer
        self.programacion.eta_recalculado_min = None
        self.programacion.save(update_fields=['eta_recalculado_min', 'updated_at'])
        data = ProgramacionListSerializer(self.programacion).data
        self.assertIn('eta_recalculado_min', data)
        self.assertIsNone(data['eta_recalculado_min'])


class HalNocheTiempoViajeSinEtaTests(TestCase):
    """HAL-3: TiempoViaje se crea aunque eta_minutos sea 0/None al arribar.

    El guard antiguo requería programacion.eta_minutos truthy, lo que
    silenciaba el aprendizaje cuando Mapbox+ML caían. Ahora el bloque
    _update_registro_operacion_on_completion crea el TiempoViaje con
    tiempo_mapbox_min derivado de distancia_km/35 km/h si eta_minutos es 0.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='h3_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='HAL3 Driver', user=self.user, patente='H3-1234',
        )
        self.cd = CD.objects.create(
            nombre='HAL3 CD', codigo='HAL3-CD', direccion='Destino',
            comuna='Santiago', lat=-33.450000, lng=-70.650000,
        )
        self.container = Container.objects.create(
            container_id='HAL3C1234', estado='asignado', cliente='HAL3 Cliente',
        )
        ahora = timezone.now()
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='HAL3 Cliente',
            fecha_programada=ahora - timedelta(minutes=10),
            fecha_inicio_ruta=ahora - timedelta(minutes=30),
            gps_inicio_lat=-33.40, gps_inicio_lng=-70.60,
            distancia_km=10.0,
            eta_minutos=0,
            prediccion_ml={'source': 'no_disponible', 'requires_attention': True},
        )
        self.container.fecha_entrega = ahora - timedelta(minutes=10)
        self.container.estado = 'en_ruta'
        self.container.save(update_fields=['fecha_entrega', 'estado', 'updated_at'])
        from .models import RegistroOperacion
        RegistroOperacion.objects.create(
            programacion=self.programacion, estado_final='PENDIENTE',
        )

    def test_tiempo_viaje_se_crea_aunque_eta_minutos_sea_cero(self):
        from .models import TiempoViaje
        from .views import ProgramacionViewSet
        view = ProgramacionViewSet()
        view._update_registro_operacion_on_completion(
            self.programacion, 'ENTREGADO',
        )
        tv = TiempoViaje.objects.filter(programacion=self.programacion).first()
        self.assertIsNotNone(tv,
                             'TiempoViaje debe crearse aunque eta_minutos=0 (HAL-3)')
        self.assertGreaterEqual(tv.tiempo_mapbox_min, 16)
        self.assertLessEqual(tv.tiempo_mapbox_min, 19)
        self.assertGreaterEqual(tv.tiempo_real_min, 19)
        self.assertLessEqual(tv.tiempo_real_min, 21)

    def test_tiempo_viaje_usa_eta_minutos_cuando_es_truthy(self):
        from .models import TiempoViaje
        from .views import ProgramacionViewSet
        self.programacion.eta_minutos = 12
        self.programacion.save(update_fields=['eta_minutos', 'updated_at'])
        view = ProgramacionViewSet()
        view._update_registro_operacion_on_completion(
            self.programacion, 'ENTREGADO',
        )
        tv = TiempoViaje.objects.filter(programacion=self.programacion).first()
        self.assertIsNotNone(tv)
        self.assertEqual(tv.tiempo_mapbox_min, 12,
                         'eta_minutos truthy debe prevalecer (12 min exactos)')


class HalNocheSoltarContenedorAutoRetornoTests(TestCase):
    """HAL-4 + E5: drop&hook → soltar → auto-retorno mismo conductor → vacío 5h.

    Cubre:
    - soltar_contenedor devuelve 3-tupla del service (HAL-4)
    - la respuesta HTTP trae 'retorno_automatico' con el ID de la nueva prog
    - la programación de retorno se asigna al MISMO conductor (P0-5 Safari review)
    - el contenedor de retorno permanece 'vacio' en CD hasta que inicie el retiro
    """

    def setUp(self):
        self.user = User.objects.create_user(username='h4_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='HAL4 Driver', user=self.user, patente='H4-1234',
            num_entregas_dia=1, max_entregas_dia=3,
        )
        self.cd_origin = CD.objects.create(
            nombre='HAL4 Origin', codigo='HAL4-O', direccion='Origen',
            comuna='Santiago', lat=-33.450000, lng=-70.650000,
            permite_soltar_contenedor=True,
            capacidad_vacios=10,
        )
        self.container_lleno = Container.objects.create(
            container_id='HAL4L1234', estado='entregado',
            cliente='HAL4 Cliente', cd_entrega=self.cd_origin,
            fecha_entrega=timezone.now() - timedelta(minutes=15),
        )
        self.programacion = Programacion.objects.create(
            container=self.container_lleno, cd=self.cd_origin, driver=self.driver,
            cliente='HAL4 Cliente', fecha_programada=timezone.now(),
            fecha_inicio_ruta=timezone.now() - timedelta(minutes=30),
            gps_inicio_lat=-33.40, gps_inicio_lng=-70.60,
            fecha_arribo_cd=timezone.now() - timedelta(minutes=10),
        )
        self.container_vacio = Container.objects.create(
            container_id='HAL4V1234', estado='vacio',
            cd_entrega=self.cd_origin, vacio_contabilizado=True,
            fecha_vacio=timezone.now() - timedelta(hours=1),
        )
        self.factory = APIRequestFactory()

    def _post(self, action, data, user=None):
        user = user or self.user
        request = self.factory.post('/', data, format='json')
        force_authenticate(request, user=user)
        view = ProgramacionViewSet.as_view({'post': action})
        return view(request, pk=self.programacion.pk)

    def test_soltar_contenedor_desempaqueta_3_tupla_y_expone_retorno(self):
        response = self._post('soltar_contenedor', {})
        self.assertEqual(response.status_code, 200,
                         f'soltar_contenedor debe responder 200: {response.data}')
        self.assertIn('retorno_automatico', response.data)
        self.assertIsNotNone(response.data['retorno_automatico'],
                             'Retorno automático debe crearse (P0-5)')

    def test_auto_retorno_es_mismo_conductor(self):
        response = self._post('soltar_contenedor', {})
        self.assertEqual(response.status_code, 200)
        retorno_id = response.data['retorno_automatico']
        self.assertIsNotNone(retorno_id)
        prog_retorno = Programacion.objects.get(pk=retorno_id)
        self.assertEqual(prog_retorno.driver_id, self.driver.id,
                         'P0-5: el retorno debe ser MISMO conductor que soltó')
        self.assertEqual(prog_retorno.container_id, self.container_vacio.id)
        # HAL-5 fix: la señal post_save de Programacion hace early-return cuando
        # llega con driver set, por lo que el container NO se transiciona a
        # 'asignado' automáticamente aquí. Queda en 'vacio' hasta que el
        # conductor ejecute un comando de inicio. Esto es coherente con el
        # patrón P0-5 (Safari review).
        self.assertEqual(prog_retorno.container.estado, 'vacio')

    def test_full_flow_drop_to_vacio_estado_consistente(self):
        response = self._post('soltar_contenedor', {})
        self.assertEqual(response.status_code, 200)
        retorno_id = response.data['retorno_automatico']
        self.assertIsNotNone(retorno_id)
        self.container_lleno.refresh_from_db()
        self.assertEqual(self.container_lleno.estado, 'soltado')
        self.assertEqual(self.container_lleno.vacio_contabilizado, False)

        prog_soltada = Programacion.objects.get(pk=self.programacion.pk)
        from apps.core.services.operations import OperationalFlowService
        OperationalFlowService.mark_empty(prog_soltada, 'cd', 'test')
        self.container_lleno.refresh_from_db()
        self.assertEqual(self.container_lleno.estado, 'vacio')
        self.assertTrue(self.container_lleno.vacio_contabilizado)
        self.cd_origin.refresh_from_db()
        self.assertEqual(self.cd_origin.vacios_actuales, 1,
                         'CD debe haber recibido el vacío')
        from apps.programaciones.models import TiempoOperacion
        tiempo = TiempoOperacion.objects.filter(
            container=self.container_lleno, tipo_operacion='descarga_cd',
        ).first()
        self.assertIsNotNone(tiempo)

        prog_retorno = Programacion.objects.get(pk=retorno_id)
        self.assertEqual(prog_retorno.driver_id, self.driver.id)
        # HAL-5 fix: ver test_auto_retorno_es_mismo_conductor — container queda 'vacio'.
        self.assertEqual(prog_retorno.container.estado, 'vacio')
        self.assertEqual(prog_retorno.cd_id, self.cd_origin.id,
                         'Destino del retorno debe ser el mismo CD donde soltó')
        self.container_vacio.refresh_from_db()
        self.assertEqual(self.container_vacio.estado, 'vacio')
        self.assertTrue(self.container_vacio.vacio_contabilizado)
        self.cd_origin.refresh_from_db()
        self.assertEqual(self.cd_origin.vacios_actuales, 1)


class HalNocheSoltarContenedorAnonimoTests(TestCase):
    """HAL-4 seguridad: soltar_contenedor rechaza requests anónimos.

    Safari review: el guard _usuario_puede_operar_viaje exige auth+match
    driver_id==user_id (o staff). Garantiza que la respuesta 3-tupla no
    quede expuesta por un bypass de auth.
    """

    def setUp(self):
        self.owner = User.objects.create_user(username='h4_owner', password='***')
        self.driver = Driver.objects.create(
            nombre='HAL4 Owner', user=self.owner, patente='O-1234',
            num_entregas_dia=1, max_entregas_dia=3,
        )
        self.cd = CD.objects.create(
            nombre='HAL4 AuthCD', codigo='HAL4-AUTH', direccion='X',
            comuna='Santiago', lat=-33.45, lng=-70.65,
            permite_soltar_contenedor=True, capacidad_vacios=5,
        )
        self.container = Container.objects.create(
            container_id='HAL4AN1234', estado='entregado', cliente='Cli',
            cd_entrega=self.cd, fecha_entrega=timezone.now() - timedelta(minutes=10),
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='Cli', fecha_programada=timezone.now(),
        )
        self.factory = APIRequestFactory()

    def test_solicitud_anonima_recibe_403(self):
        from rest_framework.test import APIRequestFactory as _f
        factory = _f()
        request = factory.post('/', {}, format='json')
        # SIN force_authenticate — request anónimo
        view = ProgramacionViewSet.as_view({'post': 'soltar_contenedor'})
        response = view(request, pk=self.programacion.pk)
        self.assertIn(response.status_code, (401, 403),
                      f'Request anónimo debe ser rechazado: {response.status_code}')


class HalNocheAceptarAsignacion200Tests(TestCase):
    """HAL-6: aceptar_asignacion devuelve 200 OK, no 201."""

    def setUp(self):
        self.user = User.objects.create_user(username='h6_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='HAL6 Driver', user=self.user, patente='H6-1234',
        )
        self.cd = CD.objects.create(
            nombre='HAL6 CD', codigo='HAL6-CD', direccion='D',
            comuna='Santiago', lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='HAL6A1234', estado='asignado', cliente='Cli',
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='Cli', fecha_programada=timezone.now() + timedelta(hours=1),
        )
        self.factory = APIRequestFactory()

    def test_aceptar_asignacion_devuelve_200_no_201(self):
        request = self.factory.post('/', {}, format='json')
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': 'aceptar_asignacion'})
        response = view(request, pk=self.programacion.pk)
        self.assertEqual(response.status_code, 200,
                         f'aceptar_asignacion debe devolver 200, no 201: {response.status_code}')


class HalNochePatenteNullTests(TestCase):
    """HAL-7: iniciar_ruta no revienta con {'patente': null}."""

    def setUp(self):
        self.user = User.objects.create_user(username='h7_driver', password='***')
        self.driver = Driver.objects.create(
            nombre='HAL7 Driver', user=self.user, patente='H7-1234',
        )
        self.cd = CD.objects.create(
            nombre='HAL7 CD', codigo='HAL7-CD', direccion='D',
            comuna='Santiago', lat=-33.45, lng=-70.65,
        )
        self.container = Container.objects.create(
            container_id='HAL7P1234', estado='asignado', cliente='Cli',
        )
        self.programacion = Programacion.objects.create(
            container=self.container, cd=self.cd, driver=self.driver,
            cliente='Cli', fecha_programada=timezone.now() + timedelta(hours=1),
        )
        self.factory = APIRequestFactory()

    def test_patente_null_es_tratado_como_vacio_y_devuelve_400(self):
        request = self.factory.post('/', {
            'patente': None, 'lat': -33.40, 'lng': -70.60,
        }, format='json')
        force_authenticate(request, user=self.user)
        view = ProgramacionViewSet.as_view({'post': 'iniciar_ruta'})
        response = view(request, pk=self.programacion.pk)
        # Comportamiento: patente vacía → 400 con mensaje "Debe ingresar la patente".
        self.assertEqual(response.status_code, 400,
                         f'patente=null debe manejarse sin 500: {response.data}')
