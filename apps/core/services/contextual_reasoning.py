import logging
from dataclasses import dataclass
from typing import List
from django.db.models import Q

from apps.programaciones.models import Programacion

logger = logging.getLogger(__name__)

@dataclass
class SimilarCase:
    id: int
    similarity: float
    outcome: str

class ContextualReasoningService:
    @staticmethod
    def infer_outcome_from_container_state(item: Programacion) -> str:
        '''
        Infiere el resultado de una programación basándose en su estado final o el de su contenedor.
        '''
        if item.estado_final and item.estado_final in ['ENTREGADO', 'PARCIAL', 'FALLIDO']:
            return item.estado_final

        # Mapeo de estados de contenedor a resultados de programación
        container_state_map = {
            'entregado': 'ENTREGADO',
            'descargado': 'ENTREGADO',
            'devuelto': 'ENTREGADO',
            'incidente': 'FALLIDO',
            'cancelado': 'FALLIDO',
        }

        outcome = container_state_map.get(item.container.estado)

        if outcome:
            return outcome

        logger.debug(f"No se pudo inferir un resultado final para la programación {item.id} con estado de contenedor '{item.container.estado}'. Se asume 'DESCONOCIDO'.")
        return 'DESCONOCIDO'

    @classmethod
    def dynamic_weights(cls, base_weights: dict, programacion: Programacion) -> dict:
        '''
        Ajusta dinámicamente los pesos de los criterios de asignación según el contexto de la programación.
        '''
        weights = dict(base_weights)

        # Ajustes por urgencia
        if programacion.urgencia_servicio == 'CRITICO':
            weights['riesgo_de_atraso'] = min(1.0, weights.get('riesgo_de_atraso', 0) + 0.05)
            weights['urgencia_del_servicio'] = min(1.0, weights.get('urgencia_del_servicio', 0) + 0.05)
            weights['historial_operativo'] = max(0.0, weights.get('historial_operativo', 0) - 0.05)
            weights['adecuacion_vehiculo_carga'] = max(0.0, weights.get('adecuacion_vehiculo_carga', 0) - 0.05)
        elif programacion.urgencia_servicio == 'URGENTE':
            weights['riesgo_de_atraso'] = min(1.0, weights.get('riesgo_de_atraso', 0) + 0.03)
            weights['urgencia_del_servicio'] = min(1.0, weights.get('urgencia_del_servicio', 0) + 0.02)
            weights['historial_operativo'] = max(0.0, weights.get('historial_operativo', 0) - 0.03)
            weights['adecuacion_vehiculo_carga'] = max(0.0, weights.get('adecuacion_vehiculo_carga', 0) - 0.02)

        # Ajustes por seguimiento especial
        if programacion.requiere_seguimiento_especial:
            weights['disponibilidad_confirmada'] = min(1.0, weights.get('disponibilidad_confirmada', 0) + 0.04)
            weights['riesgo_de_atraso'] = min(1.0, weights.get('riesgo_de_atraso', 0) + 0.03)
            weights['urgencia_del_servicio'] = max(0.0, weights.get('urgencia_del_servicio', 0) - 0.04)
            weights['historial_operativo'] = max(0.0, weights.get('historial_operativo', 0) - 0.03)

        # Normalización para asegurar que la suma de los pesos sea 1.0
        total = sum(weights.values())
        if total == 0:
            logger.warning("La suma de pesos dinámicos es cero. Se devolverán los pesos base.")
            return base_weights

        return {k: round(v / total, 4) for k, v in weights.items()}

    @classmethod
    def similar_cases(cls, programacion: Programacion, top_n: int = 5) -> List[SimilarCase]:
        '''
        Encuentra los casos históricos más similares a la programación actual.
        '''
        try:
            # Estados finales que indican que una operación ha concluido
            final_states = ['entregado', 'descargado', 'devuelto', 'incidente', 'cancelado']

            base_qs = Programacion.objects.filter(
                container__estado__in=final_states
            ).exclude(pk=programacion.pk).select_related('container', 'cd', 'driver')

            # Filtro más específico para encontrar candidatos relevantes
            candidates = base_qs.filter(
                Q(cd_id=programacion.cd_id) |
                Q(container__tipo=programacion.container.tipo)
            ).order_by('-fecha_programada')[:150]

            if not candidates:
                logger.info(f"No se encontraron casos similares para la programación {programacion.id}.")
                return []

            scored = []
            for item in candidates:
                sim = 0.0
                # Ponderaciones de similitud
                if item.cd_id == programacion.cd_id:
                    sim += 0.35
                if item.container.tipo == programacion.container.tipo:
                    sim += 0.25
                if item.container.vendor and item.container.vendor == programacion.container.vendor:
                    sim += 0.15
                if item.urgencia_servicio == programacion.urgencia_servicio:
                    sim += 0.15
                if item.cliente == programacion.cliente:
                    sim += 0.10

                outcome = cls.infer_outcome_from_container_state(item)
                if outcome != 'DESCONOCIDO':
                    scored.append(SimilarCase(item.id, round(sim, 3), outcome))

            scored.sort(key=lambda x: x.similarity, reverse=True)
            return scored[:top_n]
        except Exception as e:
            logger.error(f"Error al buscar casos similares para la programación {programacion.id}: {e}", exc_info=True)
            return []

    @classmethod
    def confidence(cls, similar_cases: List[SimilarCase]) -> float:
        '''
        Calcula un nivel de confianza basado en la densidad y consistencia de los casos similares.
        '''
        if not similar_cases:
            return 0.25  # Confianza base mínima si no hay casos similares

        # Densidad: qué tan parecidos son los casos encontrados
        similarities = [c.similarity for c in similar_cases]
        density = sum(similarities) / len(similarities) if similarities else 0

        # Consistencia: qué tan consistentes son los resultados de esos casos
        outcomes = [c.outcome for c in similar_cases]
        if not outcomes:
            return round(density * 0.5, 3) # Si no hay resultados, la confianza se basa solo en la densidad

        # Contar resultados positivos vs. negativos/parciales
        positive_outcomes = outcomes.count('ENTREGADO')
        total_outcomes = len(outcomes)

        consistency = positive_outcomes / total_outcomes if total_outcomes > 0 else 0

        # Fórmula de confianza ponderada
        confidence = (density * 0.6) + (consistency * 0.4)

        # Asegurar que la confianza esté en un rango razonable [0.1, 0.95]
        return round(max(0.1, min(0.95, confidence)), 3)
