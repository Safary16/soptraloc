"""Motor híbrido de aprendizaje operacional, explicable y con fallback seguro."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from math import exp
from statistics import median

from django.utils import timezone

from apps.core.services.mapbox import MapboxService
from apps.programaciones.models import TiempoViaje


class OperationalLearningEngine:
    """Aprende factores reales por tramo, horario, ruta y conductor."""

    HISTORY_DAYS = 120
    MIN_ROUTE_SAMPLES = 2
    MIN_DRIVER_SAMPLES = 3

    @classmethod
    def _near(cls, value, target, radius=0.012):
        return target - radius <= float(value) <= target + radius

    @classmethod
    def _history(cls, origin, destination):
        cutoff = timezone.now().date() - timedelta(days=cls.HISTORY_DAYS)
        rows = TiempoViaje.objects.filter(anomalia=False, fecha__gte=cutoff).select_related('conductor')
        return [
            row for row in rows
            if cls._near(row.origen_lat, float(origin[0]))
            and cls._near(row.origen_lon, float(origin[1]))
            and cls._near(row.destino_lat, float(destination[0]))
            and cls._near(row.destino_lon, float(destination[1]))
            and row.tiempo_mapbox_min > 0
            and row.tiempo_real_min > 0
        ]

    @staticmethod
    def _circular_hour_distance(left, right):
        delta = abs(left - right)
        return min(delta, 24 - delta)

    @classmethod
    def _weighted_factor(cls, rows, departure, driver=None, route_signature=None):
        weighted = []
        for row in rows:
            factor = max(0.45, min(2.5, row.calcular_factor_correccion()))
            age_days = max(0, (timezone.now().date() - row.fecha).days)
            weight = exp(-age_days / 75)
            hour_distance = cls._circular_hour_distance(row.hora_del_dia, departure.hour)
            weight *= exp(-hour_distance / 3.0)
            weight *= 1.35 if row.dia_semana == departure.weekday() else 0.82
            if route_signature and row.ruta_firma == route_signature:
                weight *= 1.8
            if driver and row.conductor_id == driver.id:
                weight *= 1.65
            weighted.append((factor, weight))
        if not weighted:
            return 1.0
        total_weight = sum(weight for _, weight in weighted)
        return sum(factor * weight for factor, weight in weighted) / total_weight

    @classmethod
    def driver_profile(cls, driver, rows=None):
        rows = rows if rows is not None else list(
            TiempoViaje.objects.filter(conductor=driver, anomalia=False).order_by('-fecha')[:40]
        )
        factors = [r.calcular_factor_correccion() for r in rows if r.tiempo_mapbox_min > 0]
        samples = len(factors)
        if samples < cls.MIN_DRIVER_SAMPLES:
            return {
                'samples': samples, 'factor': 1.0, 'label': 'sin_datos_suficientes',
                'confidence': round(min(0.35, samples / 10), 2),
            }
        factor = float(median(factors))
        if factor <= 0.92:
            label = 'más_rápido_que_referencia'
        elif factor >= 1.12:
            label = 'más_lento_que_referencia'
        else:
            label = 'ritmo_esperado'
        return {
            'samples': samples,
            'factor': round(factor, 3),
            'label': label,
            'confidence': round(min(0.95, 0.35 + samples / 30), 2),
        }

    @classmethod
    def predict_route(cls, origin, destination, departure, base_route, driver=None, history=None):
        history = history if history is not None else cls._history(origin, destination)
        signature = base_route.get('route_signature')
        route_rows = [r for r in history if signature and r.ruta_firma == signature]
        relevant = route_rows if len(route_rows) >= cls.MIN_ROUTE_SAMPLES else history
        learned_factor = cls._weighted_factor(
            relevant, departure, driver=driver, route_signature=signature
        )
        samples = len(relevant)
        # Mezcla progresiva: Mapbox domina al inicio; el histórico gana peso al madurar.
        learned_weight = min(0.78, samples / 18)
        blended_factor = (1 - learned_weight) + learned_weight * learned_factor
        predicted = max(1, round(float(base_route['duration_minutes']) * blended_factor))
        confidence = min(0.96, 0.25 + samples / 24)
        return {
            **base_route,
            'predicted_minutes': predicted,
            'mapbox_minutes': float(base_route['duration_minutes']),
            'learned_factor': round(learned_factor, 3),
            'samples': samples,
            'confidence': round(confidence, 2),
            'source': 'hybrid_ml_mapbox' if samples else 'mapbox_cold_start',
            'driver_profile': cls.driver_profile(driver, relevant) if driver else None,
        }

    @classmethod
    def recommend(cls, origin, destination, departure, driver=None, window_hours=3):
        mapbox = MapboxService.calcular_rutas_alternativas(
            float(origin[1]), float(origin[0]), float(destination[1]), float(destination[0])
        )
        if not mapbox.get('success'):
            fallback = MapboxService.calcular_ruta(
                float(origin[1]), float(origin[0]), float(destination[1]), float(destination[0])
            )
            if not fallback.get('success'):
                return {'success': False, 'error': fallback.get('error') or mapbox.get('error')}
            routes = [{**fallback, 'route_index': 0}]
        else:
            routes = mapbox['routes']

        history = cls._history(origin, destination)
        candidates = []
        for hour_offset in range(max(0, int(window_hours)) + 1):
            candidate_departure = departure + timedelta(hours=hour_offset)
            for route in routes:
                candidate = cls.predict_route(
                    origin, destination, candidate_departure, route,
                    driver=driver, history=history,
                )
                candidate['departure'] = candidate_departure
                candidates.append(candidate)
        candidates.sort(key=lambda item: (item['predicted_minutes'], item['distance_km']))
        best = candidates[0]
        return {
            'success': True,
            'recommended': best,
            'alternatives': candidates[1:6],
            'history_samples': len(history),
            'cold_start': len(history) < 3,
            'explanation': (
                f"Recomendación basada en {len(history)} viajes válidos; "
                f"Mapbox {best['mapbox_minutes']:.0f} min, predicción {best['predicted_minutes']} min, "
                f"confianza {best['confidence']:.0%}."
            ),
        }

    @classmethod
    def rank_drivers(cls, drivers, origin, destination, departure, base_route):
        history = cls._history(origin, destination)
        ranked = []
        for driver in drivers:
            prediction = cls.predict_route(
                origin, destination, departure, base_route, driver=driver, history=history
            )
            ranked.append({
                'driver': driver,
                'predicted_minutes': prediction['predicted_minutes'],
                'confidence': prediction['confidence'],
                'profile': prediction['driver_profile'],
            })
        return sorted(ranked, key=lambda item: (item['predicted_minutes'], -item['confidence']))
