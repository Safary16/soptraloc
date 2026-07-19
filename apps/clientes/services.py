from datetime import datetime, timedelta
from statistics import median

from django.db.models import Count
from django.utils import timezone

from apps.programaciones.models import Programacion, TiempoOperacion


class ClientSlotRecommendationService:
    """Recomendaciones explicables; reglas seguras en cold start, histórico al madurar."""

    MIN_PREDICTIVE_SAMPLES = 3
    HISTORY_DAYS = 120

    @classmethod
    def recommend(cls, empresa, cd, target_date):
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.combine(target_date, empresa.hora_inicio_recepcion), tz)
        end = timezone.make_aware(datetime.combine(target_date, empresa.hora_fin_recepcion), tz)
        now = timezone.now()
        duration = timedelta(minutes=empresa.duracion_slot_min)

        cutoff = now - timedelta(days=cls.HISTORY_DAYS)
        history = list(TiempoOperacion.objects.filter(
            cd=cd, anomalia=False, hora_inicio__gte=cutoff,
            tiempo_real_min__gt=0,
        ).only('hora_inicio', 'tiempo_real_min'))
        baseline = float(median([row.tiempo_real_min for row in history])) if history else float(cd.tiempo_promedio_descarga_min or 60)

        candidates = []
        cursor = start
        while cursor + duration <= end:
            if cursor > now:
                slot_end = cursor + duration
                load = Programacion.objects.filter(
                    cd=cd,
                    fecha_programada__lt=slot_end,
                    fecha_programada__gte=cursor,
                ).exclude(container__estado__in=['cancelado', 'devuelto']).count()
                same_hour = [
                    row.tiempo_real_min for row in history
                    if row.hora_inicio.weekday() == cursor.weekday()
                    and abs(row.hora_inicio.hour - cursor.hour) <= 1
                ]
                samples = len(same_hour)
                predicted_duration = float(median(same_hour)) if samples else baseline
                capacity = max(1, empresa.capacidad_por_slot)
                available = max(0, capacity - load)
                load_score = max(0, 70 * (available / capacity))
                duration_score = max(0, 30 * min(1.0, baseline / max(1.0, predicted_duration)))
                confidence = min(0.95, 0.30 + samples / 12) if samples else 0.25
                source = 'historico_operacional' if samples >= cls.MIN_PREDICTIVE_SAMPLES else 'reglas_capacidad'
                candidates.append({
                    'inicio': cursor.isoformat(),
                    'fin': slot_end.isoformat(),
                    'cupos_disponibles': available,
                    'capacidad': capacity,
                    'carga_programada': load,
                    'duracion_estimada_min': round(predicted_duration),
                    'score': round(load_score + duration_score, 1),
                    'confianza': round(confidence, 2),
                    'muestras': samples,
                    'fuente': source,
                    'disponible': available > 0,
                    'explicacion': (
                        f'{available} de {capacity} cupos disponibles; '
                        f'descarga estimada en {round(predicted_duration)} min. '
                        + (f'Basado en {samples} operaciones comparables.' if source == 'historico_operacional'
                           else 'Estimación inicial por capacidad; aún faltan históricos suficientes.')
                    ),
                })
            cursor += duration

        candidates.sort(key=lambda item: (not item['disponible'], -item['score'], item['inicio']))
        return {
            'fecha': target_date.isoformat(),
            'cold_start': len(history) < cls.MIN_PREDICTIVE_SAMPLES,
            'muestras_totales': len(history),
            'recomendados': candidates[:3],
            'todos': candidates,
        }
