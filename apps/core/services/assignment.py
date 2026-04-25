from decimal import Decimal
from django.conf import settings
from django.utils import timezone

from apps.drivers.models import Driver
from apps.programaciones.models import Programacion, RegistroOperacion
from apps.core.services.mapbox import MapboxService
from apps.core.services.ml_predictor import MLTimePredictor
from apps.core.services.anomaly_detector import (
    AnomalyDetector, DelayRiskScorer, CapacityChecker, ETAEstimator, RouteFeasibilityValidator
)
from apps.core.services.contextual_reasoning import ContextualReasoningService


class AssignmentService:
    DEFAULT_WEIGHTS = {
        'disponibilidad_confirmada': 0.30,
        'riesgo_de_atraso': 0.25,
        'adecuacion_vehiculo_carga': 0.20,
        'historial_operativo': 0.15,
        'urgencia_del_servicio': 0.10,
    }

    @classmethod
    def _get_base_weights(cls) -> dict:
        return {
            'disponibilidad_confirmada': float(getattr(settings, 'PESO_DISPONIBILIDAD_CONFIRMADA', cls.DEFAULT_WEIGHTS['disponibilidad_confirmada'])),
            'riesgo_de_atraso': float(getattr(settings, 'PESO_RIESGO_ATRASO', cls.DEFAULT_WEIGHTS['riesgo_de_atraso'])),
            'adecuacion_vehiculo_carga': float(getattr(settings, 'PESO_ADECUACION_VEHICULO_CARGA', cls.DEFAULT_WEIGHTS['adecuacion_vehiculo_carga'])),
            'historial_operativo': float(getattr(settings, 'PESO_HISTORIAL_OPERATIVO', cls.DEFAULT_WEIGHTS['historial_operativo'])),
            'urgencia_del_servicio': float(getattr(settings, 'PESO_URGENCIA_SERVICIO', cls.DEFAULT_WEIGHTS['urgencia_del_servicio'])),
        }

    @classmethod
    def _score_disponibilidad(cls, driver: Driver) -> float:
        return 1.0 if CapacityChecker.has_capacity(driver) else 0.0

    @classmethod
    def _score_riesgo(cls, programacion: Programacion, driver: Driver) -> float:
        return max(0.0, 1.0 - DelayRiskScorer.score(programacion, driver))

    @classmethod
    def _score_adecuacion(cls, programacion: Programacion, driver: Driver) -> float:
        capacidad_base_ton = float(getattr(settings, 'VEHICLE_DEFAULT_CAPACITY_TON', 28))
        peso = float(programacion.container.peso_total_tons)
        if peso <= 0:
            return 0.7
        ratio = min(1.0, peso / capacidad_base_ton)
        # penalizar sobrecapacidad
        if peso > capacidad_base_ton:
            return 0.0
        return round(1.0 - (ratio * 0.35), 3)

    @classmethod
    def _score_historial(cls, driver: Driver) -> float:
        return round(float(driver.cumplimiento_porcentaje) / 100.0, 3)

    @classmethod
    def _score_urgencia(cls, programacion: Programacion) -> float:
        if programacion.urgencia_servicio == 'CRITICO':
            return 1.0
        if programacion.urgencia_servicio == 'URGENTE':
            return 0.75
        return 0.5

    @classmethod
    def _classify(cls, score: float, anomalies: list[dict], confidence: float) -> str:
        severities = {a['severity'] for a in anomalies}
        if 'P0' in severities or 'P1' in severities:
            return 'INTERVENCION'
        if confidence < float(getattr(settings, 'MIN_CONFIDENCE_AUTO_DISPATCH', 0.55)):
            return 'REVISION_OPERADOR'
        if score >= 0.75:
            return 'DESPACHO_DIRECTO'
        if score < 0.45:
            return 'INTERVENCION'
        return 'REVISION_OPERADOR'

    @classmethod
    def _build_reason(cls, driver: Driver, score: float, classification: str, anomalies: list[dict], confidence: float) -> str:
        if classification == 'DESPACHO_DIRECTO':
            return f"{driver.nombre} cumple condiciones para despacho directo (score {score:.2f}, confianza {confidence:.2f})."
        if classification == 'REVISION_OPERADOR':
            return f"{driver.nombre} recomendado con revisión de operador (score {score:.2f}, confianza {confidence:.2f})."
        if anomalies:
            top = anomalies[0]
            return f"Intervención requerida por {top['code']} - {top['message']}"
        return f"Intervención requerida por score bajo ({score:.2f})."

    @classmethod
    def calcular_score_total(cls, driver: Driver, programacion: Programacion):
        base_weights = cls._get_base_weights()
        dyn_weights = ContextualReasoningService.dynamic_weights(base_weights, programacion)

        dimensions = {
            'disponibilidad_confirmada': cls._score_disponibilidad(driver),
            'riesgo_de_atraso': cls._score_riesgo(programacion, driver),
            'adecuacion_vehiculo_carga': cls._score_adecuacion(programacion, driver),
            'historial_operativo': cls._score_historial(driver),
            'urgencia_del_servicio': cls._score_urgencia(programacion),
        }

        deterministic = sum(dimensions[k] * dyn_weights[k] for k in dimensions)
        similar_cases = ContextualReasoningService.similar_cases(programacion, top_n=5)
        confidence = ContextualReasoningService.confidence(similar_cases)
        similar_boost = (sum(c.similarity for c in similar_cases) / len(similar_cases)) if similar_cases else 0.0
        final_score = round((deterministic * 0.8) + (similar_boost * 0.2), 3)

        anomalies = AnomalyDetector.detect(programacion, driver)
        classification = cls._classify(final_score, anomalies, confidence)
        reason = cls._build_reason(driver, final_score, classification, anomalies, confidence)

        return {
            'score_total': Decimal(str(final_score)),
            'score_por_dimension': dimensions,
            'weights': dyn_weights,
            'anomalies': anomalies,
            'classification': classification,
            'confidence': confidence,
            'similar_cases': [
                {'programacion_id': c.programacion_id, 'similarity': c.similarity, 'outcome': c.outcome}
                for c in similar_cases
            ],
            'reason': reason,
            'eta_estimado_min': ETAEstimator.estimate_minutes(programacion, driver),
            'factible': RouteFeasibilityValidator.is_feasible(programacion, ETAEstimator.estimate_minutes(programacion, driver)),
        }

    @classmethod
    def obtener_conductores_disponibles_con_score(cls, programacion: Programacion):
        drivers = Driver.objects.filter(activo=True, presente=True)
        resultados = []
        for driver in drivers:
            score_data = cls.calcular_score_total(driver, programacion)
            resultados.append({
                'driver': driver,
                'score': score_data['score_total'],
                'desglose': score_data['score_por_dimension'],
                'weights': score_data['weights'],
                'anomalies': score_data['anomalies'],
                'classification': score_data['classification'],
                'confidence': score_data['confidence'],
                'similar_cases': score_data['similar_cases'],
                'reason': score_data['reason'],
                'eta_estimado_min': score_data['eta_estimado_min'],
            })
        resultados.sort(key=lambda x: x['score'], reverse=True)
        return resultados

    @classmethod
    def _persist_operation_log(cls, programacion: Programacion, candidate: dict, decision_operador='PENDIENTE', motivo_override=''):
        driver = candidate['driver']
        RegistroOperacion.objects.create(
            programacion=programacion,
            service_id=str(programacion.id),
            recurso_asignado=driver.nombre,
            score_por_dimension=candidate['desglose'],
            clasificacion_sistema=candidate['classification'],
            decision_operador=decision_operador,
            motivo_override=motivo_override,
            anomalias_detectadas=candidate['anomalies'],
            similitud_historica_usada=candidate['similar_cases'],
            timestamp_despacho=timezone.now(),
            eta_estimado_min=candidate.get('eta_estimado_min'),
        )

    @classmethod
    def asignar_mejor_conductor(cls, programacion: Programacion, usuario=None):
        if programacion.driver:
            return {
                'success': False,
                'error': f'La programación ya tiene conductor asignado: {programacion.driver.nombre}'
            }

        conductores = cls.obtener_conductores_disponibles_con_score(programacion)
        if not conductores:
            return {'success': False, 'error': 'No hay conductores disponibles'}

        mejor = conductores[0]
        driver = mejor['driver']

        programacion.score_por_dimension = mejor['desglose']
        programacion.clasificacion_sistema = mejor['classification']
        programacion.nivel_confianza = Decimal(str(round(mejor['confidence'] * 100, 2)))
        programacion.anomalias_detectadas = mejor['anomalies']
        programacion.similitud_historica_usada = mejor['similar_cases']
        programacion.eta_recalculado_min = mejor['eta_estimado_min']
        programacion.timestamp_despacho = timezone.now()
        programacion.save(update_fields=[
            'score_por_dimension', 'clasificacion_sistema', 'nivel_confianza',
            'anomalias_detectadas', 'similitud_historica_usada', 'eta_recalculado_min', 'timestamp_despacho'
        ])

        has_blocking = any(a['severity'] in ('P0', 'P1') for a in mejor['anomalies'])
        if mejor['classification'] != 'DESPACHO_DIRECTO' or has_blocking:
            cls._persist_operation_log(programacion, mejor, decision_operador='PENDIENTE')
            return {
                'success': False,
                'requires_operator': True,
                'error': 'Requiere revisión de operador antes de despachar',
                'driver': driver,
                'score': mejor['score'],
                'desglose': mejor['desglose'],
                'classification': mejor['classification'],
                'anomalies': mejor['anomalies'],
                'similar_cases': mejor['similar_cases'],
                'confidence': mejor['confidence'],
                'reason': mejor['reason'],
                'alternatives': [
                    {
                        'driver': c['driver'].nombre,
                        'score': float(c['score']),
                        'classification': c['classification'],
                        'reason': c['reason'],
                    } for c in conductores[1:4]
                ],
            }

        programacion.asignar_conductor(driver, usuario)
        cls._persist_operation_log(programacion, mejor, decision_operador='CONFIRMAR')
        return {
            'success': True,
            'driver': driver,
            'score': mejor['score'],
            'desglose': mejor['desglose'],
            'classification': mejor['classification'],
            'anomalies': mejor['anomalies'],
            'similar_cases': mejor['similar_cases'],
            'confidence': mejor['confidence'],
            'reason': mejor['reason'],
            'alternatives': [
                {
                    'driver': c['driver'].nombre,
                    'score': float(c['score']),
                    'classification': c['classification'],
                    'reason': c['reason'],
                } for c in conductores[1:4]
            ],
        }

    @classmethod
    def asignar_multiples(cls, programaciones, usuario=None):
        resultados = {'asignadas': 0, 'fallidas': 0, 'detalles': []}
        for programacion in programaciones:
            resultado = cls.asignar_mejor_conductor(programacion, usuario)
            if resultado['success']:
                resultados['asignadas'] += 1
            else:
                resultados['fallidas'] += 1
            resultados['detalles'].append({
                'programacion_id': programacion.id,
                'container_id': programacion.container.container_id,
                'success': resultado['success'],
                'driver': resultado.get('driver').nombre if resultado.get('driver') else None,
                'score': float(resultado['score']) if resultado.get('score') else None,
                'classification': resultado.get('classification'),
                'reason': resultado.get('reason') or resultado.get('error'),
                'requires_operator': resultado.get('requires_operator', False),
            })
        return resultados
