"""
TAREA 2 — FSM audit completo (auditoría Flaco 2026-10-02, plan aprobado por safary16).

Cubre los huecos del FSM de Container que los tests existentes no protegían:
ramificaciones post-entrega, retorno vacío completo, estados terminales,
las 6 reversiones administrativas (+negativas), timestamps (setter, stale,
preservación del estado_anterior), bandera secuenciado, Event de auditoría
en reversión, y marcar_verificacion_externa.

LIMITACIÓN CONOCIDA — concurrencia: cambiar_estado() usa select_for_update()
dentro de transaction.atomic (models.py ~435) para bloquear la fila contra
transiciones duplicadas por race condition. En los tests el backend es SQLite
(config/settings.py:139) y Django NO emite SELECT ... FOR UPDATE en SQLite
(no-op). Un test de concurrencia aquí pasaría siempre aunque el lock no
existiera: un placebo que miente. Por indicación de safary16 NO se escribe
tal test; el lock queda validado por diseño (código verificado) y sería
ejercitado de verdad solo con un backend transaccional (PostgreSQL/MySQL) +
TransactionTestCase + threading.
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.containers.models import Container
from apps.events.models import Event


_SEQ = 0


def _make_container(container_id=None, estado='por_arribar'):
    global _SEQ
    _SEQ += 1
    return Container.objects.create(
        container_id=container_id or f'FSMC{_SEQ:07d}',
        tipo='40',
        tipo_carga='dry',
        nave='Nave FSM',
        estado=estado,
    )


class FSMStructuralIntegrityTests(TestCase):
    """Skill fsm-audit pasos 2-5: estados referenciados existen, terminales
    son sumideros, y el mapa de timestamps cubre los 15 estados."""

    def test_every_transition_target_is_a_defined_state(self):
        defined = {value for value, _ in Container.ESTADOS}
        for source, targets in Container.TRANSICIONES_VALIDAS.items():
            self.assertIn(source, defined,
                          f"Origen {source!r} no está en ESTADOS (estado inalcanzable)")
            for target in targets:
                self.assertIn(target, defined,
                              f"Transición {source}→{target}: destino no definido (dead-end)")

    def test_every_reversion_target_is_a_defined_state(self):
        defined = {value for value, _ in Container.ESTADOS}
        for source, targets in Container.REVERSIONES_VALIDAS.items():
            self.assertIn(source, defined)
            for target in targets:
                self.assertIn(target, defined)

    def test_terminal_states_are_true_sinks(self):
        for terminal in ('devuelto', 'cancelado'):
            self.assertEqual(Container.TRANSICIONES_VALIDAS.get(terminal), set(),
                             f"{terminal} debe ser sumidero (set())")
            self.assertNotIn(terminal, Container.REVERSIONES_VALIDAS,
                             f"{terminal} no puede tener reversiones administrativas")

    def test_timestamp_map_covers_all_states(self):
        defined = {value for value, _ in Container.ESTADOS}
        self.assertEqual(set(Container._TIMESTAMP_FIELD_BY_ESTADO), defined)


class FSMPostDeliveryBranchesTests(TestCase):
    """Ramificaciones post-entrega: entregado/soltado se dividen y el retorno
    vacío completo hasta los terminales. Hueco real: casi sin cobertura previa."""

    def test_entregado_can_branch_to_soltado_descargado_o_vacio(self):
        for target in ('soltado', 'descargado', 'vacio'):
            container = _make_container(estado='entregado')
            container.cambiar_estado(target, 'test')
            container.refresh_from_db()
            self.assertEqual(container.estado, target)

    def test_entregado_cannot_jump_to_return_states(self):
        for invalid in ('vacio_en_ruta', 'en_ccti', 'devuelto', 'programado'):
            container = _make_container(estado='entregado')
            with self.assertRaises(ValidationError):
                container.cambiar_estado(invalid, 'test')

    def test_soltado_branches(self):
        for target in ('descargado', 'vacio', 'vacio_en_ruta', 'incidente'):
            container = _make_container(estado='soltado')
            container.cambiar_estado(target, 'test')
            container.refresh_from_db()
            self.assertEqual(container.estado, target)

    def test_descargado_cannot_go_directly_to_devuelto(self):
        container = _make_container(estado='descargado')
        with self.assertRaises(ValidationError):
            container.cambiar_estado('devuelto', 'test')
        # El camino real: descargado → vacio_en_ruta → devuelto
        container.cambiar_estado('vacio_en_ruta', 'test')
        container.cambiar_estado('devuelto', 'test')
        container.refresh_from_db()
        self.assertEqual(container.estado, 'devuelto')

    def test_full_empty_return_chain(self):
        container = _make_container(estado='descargado')
        chain = ['vacio', 'vacio_en_ruta', 'en_ccti', 'vacio_en_ruta', 'devuelto']
        for target in chain:
            container.cambiar_estado(target, 'test')
        container.refresh_from_db()
        self.assertEqual(container.estado, 'devuelto')

    def test_vacio_cannot_skip_to_en_ccti_or_devuelto(self):
        for invalid in ('en_ccti', 'devuelto', 'entregado'):
            container = _make_container(estado='vacio')
            with self.assertRaises(ValidationError):
                container.cambiar_estado(invalid, 'test')

    def test_en_ccti_only_exit_is_back_to_vacio_en_ruta(self):
        container = _make_container(estado='en_ccti')
        with self.assertRaises(ValidationError):
            container.cambiar_estado('devuelto', 'test')
        container.cambiar_estado('vacio_en_ruta', 'test')
        container.refresh_from_db()
        self.assertEqual(container.estado, 'vacio_en_ruta')

    def test_incidente_can_recover_to_en_ruta_or_cancel(self):
        container = _make_container(estado='en_ruta')
        container.cambiar_estado('incidente', 'test')
        container.cambiar_estado('en_ruta', 'test')
        container.refresh_from_db()
        self.assertEqual(container.estado, 'en_ruta')
        container.cambiar_estado('incidente', 'test')
        container.cambiar_estado('cancelado', 'test')
        container.refresh_from_db()
        self.assertEqual(container.estado, 'cancelado')


class FSMTerminalStateTests(TestCase):
    """Estados terminales: ninguna salida, ni siquiera con permitir_reversion."""

    def test_devuelto_is_absolute_sink(self):
        container = _make_container(estado='devuelto')
        for target in ('vacio_en_ruta', 'por_arribar', 'liberado', 'en_ccti'):
            with self.assertRaises(ValidationError):
                container.cambiar_estado(target, 'test', permitir_reversion=True)

    def test_cancelado_is_absolute_sink(self):
        container = _make_container(estado='cancelado')
        for target in ('por_arribar', 'liberado', 'programado', 'incidente'):
            with self.assertRaises(ValidationError):
                container.cambiar_estado(target, 'test', permitir_reversion=True)

    def test_early_cancel_from_each_active_state(self):
        for source in ('por_arribar', 'liberado', 'secuenciado', 'programado',
                       'asignado', 'en_ruta'):
            container = _make_container(estado=source)
            container.cambiar_estado('cancelado', 'test')
            container.refresh_from_db()
            self.assertEqual(container.estado, 'cancelado')


class FSMReversionTests(TestCase):
    """Las 6 reversiones administrativas: funcionan SOLO con el flag, y las
    no listadas fallan incluso con el flag."""

    def _assert_reversion_works(self, desde, hacia):
        container = _make_container(estado=desde)
        container.cambiar_estado(hacia, 'admin', permitir_reversion=True)
        container.refresh_from_db()
        self.assertEqual(container.estado, hacia)
        return container

    def test_all_six_documented_reversions(self):
        self._assert_reversion_works('liberado', 'por_arribar')
        self._assert_reversion_works('secuenciado', 'por_arribar')
        self._assert_reversion_works('secuenciado', 'liberado')
        self._assert_reversion_works('programado', 'liberado')
        self._assert_reversion_works('programado', 'secuenciado')
        self._assert_reversion_works('asignado', 'programado')
        self._assert_reversion_works('en_ruta', 'asignado')
        self._assert_reversion_works('soltado', 'entregado')
        self._assert_reversion_works('en_ccti', 'vacio_en_ruta')

    def test_same_reversion_fails_without_flag(self):
        # NOTA: asignado→programado es transición válida hacia adelante
        # (TRANSICIONES_VALIDAS['asignado'] incluye 'programado'), así que
        # ahí el flag es irrelevante. Reversión real sin flag: liberado→por_arribar.
        container = _make_container(estado='liberado')
        with self.assertRaises(ValidationError):
            container.cambiar_estado('por_arribar', 'admin')

    def test_unlisted_reversion_fails_even_with_flag(self):
        # 'entregado' → 'asignado' NO está en REVERSIONES_VALIDAS: con flag
        # también debe fallar (nada más puede revertir).
        container = _make_container(estado='entregado')
        with self.assertRaises(ValidationError):
            container.cambiar_estado('asignado', 'admin', permitir_reversion=True)

    def test_devuelto_cannot_be_reverted_even_with_flag(self):
        container = _make_container(estado='devuelto')
        with self.assertRaises(ValidationError):
            container.cambiar_estado('vacio_en_ruta', 'admin', permitir_reversion=True)


class FSMReversionAuditTrailTests(TestCase):
    """Event de auditoría también en reversiones (hueco: solo se probaba en
    transiciones hacia adelante)."""

    def test_reversion_emits_audit_event_with_correct_direction(self):
        container = _make_container(estado='asignado')
        container.cambiar_estado('programado', 'operador_admin', permitir_reversion=True)
        event = Event.objects.get(
            container=container, event_type='cambio_estado'
        )
        self.assertEqual(event.detalles['estado_anterior'], 'asignado')
        self.assertEqual(event.detalles['estado_nuevo'], 'programado')
        self.assertEqual(event.usuario, 'operador_admin')


class FSMTimestampTests(TestCase):
    """Timestamps: setter del nuevo estado, limpieza de stale en reversión,
    preservación del del estado_anterior (hueco: el docstring lo describe
    pero no había test)."""

    def test_new_state_timestamp_is_set(self):
        container = _make_container(estado='por_arribar')
        container.cambiar_estado('liberado', 'test')
        container.refresh_from_db()
        self.assertIsNone(container.fecha_arribo)  # por_arribar original, sin timestamp
        self.assertIsNotNone(container.fecha_liberacion)

    def test_reversion_keeps_previous_timestamp_and_clears_older_stale(self):
        """Semántica real verificada (2026-10-02): la 'referencia histórica'
        es de UN paso — el timestamp del estado inmediatamente anterior se
        preserva (incluso en reversión), y los timestamps de estados más
        viejos se limpian en cada transición. El container se conduce por el
        FSM (no se siembra directo) para que los timestamps existan."""
        container = _make_container()
        container.cambiar_estado('liberado', 'test')
        container.cambiar_estado('programado', 'test')
        container.cambiar_estado('asignado', 'test')
        container.refresh_from_db()
        # fecha_liberacion ya fue limpiada al pasar a asignado (quedó dos
        # estados atrás — la semántica de un paso es consistente).
        self.assertIsNone(container.fecha_liberacion)
        self.assertIsNotNone(container.fecha_programacion)
        self.assertIsNotNone(container.fecha_asignacion)
        # Reversión asignado→programado: fecha_asignacion se conserva
        # (estado_anterior = referencia histórica de un paso).
        container.cambiar_estado('programado', 'admin', permitir_reversion=True)
        container.refresh_from_db()
        self.assertIsNotNone(container.fecha_asignacion)
        self.assertIsNotNone(container.fecha_programacion)
        # Segunda reversión programado→liberado: fecha_asignacion ya es
        # stale (ni nuevo ni anterior) → limpiada; fecha_programacion se
        # conserva (anterior).
        container.cambiar_estado('liberado', 'admin', permitir_reversion=True)
        container.refresh_from_db()
        self.assertIsNone(container.fecha_asignacion)  # stale: limpiado
        self.assertIsNotNone(container.fecha_programacion)  # anterior: preservado
        self.assertIsNotNone(container.fecha_liberacion)

    def test_previous_state_timestamp_is_preserved_one_step(self):
        """La preservación histórica cubre el estado INMEDIATAMENTE anterior:
        al pasar a en_ruta se conserva fecha_asignacion, pero fecha_programacion
        (dos estados atrás) se limpia por diseño — cada transición deja solo
        el timestamp nuevo y el del estado previo."""
        container = _make_container()
        container.cambiar_estado('liberado', 'test')
        container.cambiar_estado('programado', 'test')
        container.cambiar_estado('asignado', 'test')
        container.refresh_from_db()
        self.assertIsNotNone(container.fecha_programacion)  # anterior: preservado
        self.assertIsNotNone(container.fecha_asignacion)    # nuevo: seteado
        container.cambiar_estado('en_ruta', 'test')
        container.refresh_from_db()
        self.assertIsNotNone(container.fecha_asignacion)    # anterior: preservado
        self.assertIsNotNone(container.fecha_inicio_ruta)   # nuevo: seteado
        self.assertIsNone(container.fecha_programacion)     # dos atrás: limpiado por diseño

    def test_unknown_state_raises_without_side_effects(self):
        container = _make_container(estado='liberado')
        with self.assertRaises(ValidationError):
            container.cambiar_estado('estado_inexistente', 'test')
        container.refresh_from_db()
        self.assertEqual(container.estado, 'liberado')
        self.assertEqual(
            Event.objects.filter(container=container).count(), 0
        )


class FSMSequencedFlagTests(TestCase):
    """Bandera secuenciado: sync con el estado FSM al entrar y salir."""

    def test_flag_set_on_secuenciado(self):
        container = _make_container(estado='liberado')
        container.cambiar_estado('secuenciado', 'test')
        container.refresh_from_db()
        self.assertTrue(container.secuenciado)

    def test_flag_cleared_on_exit(self):
        container = _make_container(estado='secuenciado')
        container.cambiar_estado('programado', 'test')
        container.refresh_from_db()
        self.assertFalse(container.secuenciado)

    def test_flag_restored_on_reversion_to_secuenciado(self):
        container = _make_container(estado='programado')
        container.cambiar_estado('secuenciado', 'admin', permitir_reversion=True)
        container.refresh_from_db()
        self.assertTrue(container.secuenciado)
        self.assertEqual(container.estado, 'secuenciado')


class FSMExternalVerificationTests(TestCase):
    """marcar_verificacion_externa: el FSM interno queda intacto, la
    divergencia se registra, estado inválido levanta."""

    def test_verified_state_does_not_touch_fsm(self):
        container = _make_container(estado='liberado')
        resultado = container.marcar_verificacion_externa('en_ccti', 'portal_test')
        container.refresh_from_db()
        self.assertEqual(container.estado, 'liberado')  # FSM intacto
        self.assertEqual(container.estado_verificado, 'en_ccti')
        self.assertEqual(container.fuente_verificacion, 'portal_test')
        self.assertIsNotNone(container.verificado_en)
        self.assertTrue(resultado['divergencia'])

    def test_matching_state_reports_no_divergence(self):
        container = _make_container(estado='liberado')
        resultado = container.marcar_verificacion_externa('liberado', 'portal_test')
        container.refresh_from_db()
        self.assertFalse(resultado['divergencia'])

    def test_unknown_external_state_raises(self):
        container = _make_container(estado='liberado')
        with self.assertRaises(ValidationError):
            container.marcar_verificacion_externa('estado_fantasma', 'portal_test')
        container.refresh_from_db()
        self.assertIsNone(container.estado_verificado)
