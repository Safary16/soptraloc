from dataclasses import dataclass
from typing import List
from django.db.models import Q

from apps.programaciones.models import Programacion


@dataclass
class SimilarCase:
    programacion_id: int
    similarity: float
    outcome: str


class ContextualReasoningService:
    @staticmethod
    def infer_outcome_from_container_state(item: Programacion) -> str:
        if item.estado_final:
            return item.estado_final
        if item.container.estado in ['entregado', 'descargado', 'devuelto']:
            return 'ENTREGADO'
        return 'FALLIDO'

    @classmethod
    def dynamic_weights(cls, base_weights: dict, programacion: Programacion) -> dict:
        weights = dict(base_weights)

        if programacion.urgencia_servicio == 'CRITICO':
            weights['riesgo_de_atraso'] += 0.05
            weights['urgencia_del_servicio'] += 0.05
            weights['historial_operativo'] -= 0.05
            weights['adecuacion_vehiculo_carga'] -= 0.05
        elif programacion.urgencia_servicio == 'URGENTE':
            weights['riesgo_de_atraso'] += 0.03
            weights['urgencia_del_servicio'] += 0.02
            weights['historial_operativo'] -= 0.03
            weights['adecuacion_vehiculo_carga'] -= 0.02

        if programacion.requiere_seguimiento_especial:
            weights['disponibilidad_confirmada'] += 0.04
            weights['riesgo_de_atraso'] += 0.03
            weights['urgencia_del_servicio'] -= 0.04
            weights['historial_operativo'] -= 0.03

        total = sum(weights.values()) or 1.0
        return {k: round(v / total, 4) for k, v in weights.items()}

    @classmethod
    def similar_cases(cls, programacion: Programacion, top_n: int = 5) -> List[SimilarCase]:
        base_qs = Programacion.objects.filter(
            container__estado__in=['entregado', 'descargado', 'devuelto']
        ).exclude(pk=programacion.pk).select_related('container', 'cd', 'driver')

        candidates = base_qs.filter(
            Q(container__tipo=programacion.container.tipo) |
            Q(cd=programacion.cd) |
            Q(container__vendor=programacion.container.vendor)
        )[:100]

        scored = []
        for item in candidates:
            sim = 0.0
            if item.container.tipo == programacion.container.tipo:
                sim += 0.30
            if item.cd_id == programacion.cd_id:
                sim += 0.25
            if item.container.vendor and item.container.vendor == programacion.container.vendor:
                sim += 0.20
            if item.urgencia_servicio == programacion.urgencia_servicio:
                sim += 0.15
            if bool(item.driver_id) == bool(programacion.driver_id):
                sim += 0.10

            outcome = cls.infer_outcome_from_container_state(item)
            scored.append(SimilarCase(item.id, round(sim, 3), outcome))

        scored.sort(key=lambda x: x.similarity, reverse=True)
        return scored[:top_n]

    @classmethod
    def confidence(cls, similar_cases: List[SimilarCase]) -> float:
        if not similar_cases:
            return 0.25

        similarities = [c.similarity for c in similar_cases]
        density = sum(similarities) / len(similarities)
        outcomes = [c.outcome for c in similar_cases]
        consistency = max(outcomes.count('ENTREGADO'), outcomes.count('FALLIDO'), outcomes.count('PARCIAL')) / len(outcomes)
        confidence = (density * 0.7) + (consistency * 0.3)
        return round(max(0.1, min(0.95, confidence)), 3)
