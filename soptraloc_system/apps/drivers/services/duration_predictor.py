from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import pandas as pd
from django.db.models import Avg, Count
from django.utils import timezone

from ..models import Assignment, Location, TimeMatrix

try:  # pragma: no cover - la importación puede fallar en entornos sin scikit-learn
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import SGDRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except Exception:  # pragma: no cover
    ColumnTransformer = None
    SGDRegressor = None
    Pipeline = None
    OneHotEncoder = None
    StandardScaler = None


DEFAULT_FALLBACK_MINUTES = 120


@dataclass(frozen=True)
class PredictionResult:
    minutes: int
    source: str
    sample_size: int


class DriverDurationPredictor:
    """Motor de estimación híbrido para tiempos de asignación de conductores."""

    MIN_SAMPLES_FOR_MODEL = 20
    CACHE_TTL_SECONDS = 300

    def __init__(self) -> None:
        self._model: Optional[Pipeline] = None
        self._model_sample_size: int = 0
        self._dataset_cached_at: Optional[float] = None
        self._samples: Optional[pd.DataFrame] = None
        self._sklearn_available = all(
            component is not None for component in (
                ColumnTransformer,
                SGDRegressor,
                Pipeline,
                OneHotEncoder,
                StandardScaler,
            )
        )

    # ------------------------------------------------------------------
    # Dataset helpers
    # ------------------------------------------------------------------
    def _need_dataset_refresh(self) -> bool:
        if self._samples is None:
            return True
        if self._dataset_cached_at is None:
            return True
        now_ts = timezone.now().timestamp()
        return (now_ts - self._dataset_cached_at) > self.CACHE_TTL_SECONDS

    def _load_dataset(self) -> pd.DataFrame:
        if not self._need_dataset_refresh():
            return self._samples

        qs = Assignment.objects.filter(
            tiempo_real__isnull=False,
            fecha_inicio__isnull=False,
            fecha_completada__isnull=False,
            estado='COMPLETADA',
            origen__isnull=False,
            destino__isnull=False,
        ).select_related('origen', 'destino')

        records = []
        for assignment in qs:
            start = assignment.fecha_inicio or assignment.fecha_programada or assignment.fecha_asignacion
            if not start:
                continue

            scheduled = assignment.fecha_programada or start
            total_minutes = assignment.tiempo_real
            if total_minutes is None:
                continue

            records.append({
                'origin_code': assignment.origen.code,
                'destination_code': assignment.destino.code,
                'assignment_type': assignment.tipo_asignacion or 'ENTREGA',
                'hour': scheduled.astimezone(timezone.get_current_timezone()).hour,
                'weekday': scheduled.weekday(),
                'month': scheduled.month,
                'estimated_minutes': assignment.tiempo_estimado or DEFAULT_FALLBACK_MINUTES,
                'route_minutes': assignment.ruta_minutos_real or assignment.tiempo_estimado,
                'unloading_minutes': assignment.descarga_minutos_real or 0,
                'target_minutes': total_minutes,
            })

        if records:
            self._samples = pd.DataFrame.from_records(records)
        else:
            self._samples = pd.DataFrame(columns=[
                'origin_code',
                'destination_code',
                'assignment_type',
                'hour',
                'weekday',
                'month',
                'estimated_minutes',
                'route_minutes',
                'unloading_minutes',
                'target_minutes',
            ])

        self._dataset_cached_at = timezone.now().timestamp()
        return self._samples

    # ------------------------------------------------------------------
    # Historical statistics
    # ------------------------------------------------------------------
    def _historical_route_average(self, origin: Location, destination: Location, assignment_type: str) -> tuple[Optional[float], int]:
        qs = Assignment.objects.filter(
            origen=origin,
            destino=destination,
            tipo_asignacion=assignment_type,
            tiempo_real__isnull=False,
        )
        stats = qs.aggregate(avg=Avg('tiempo_real'), count=Count('id'))
        return stats['avg'], stats['count'] or 0

    def _time_matrix_estimate(self, origin: Location, destination: Location) -> Optional[int]:
        try:
            matrix = TimeMatrix.objects.get(from_location=origin, to_location=destination)
            return matrix.get_total_time()
        except TimeMatrix.DoesNotExist:
            return None

    # ------------------------------------------------------------------
    # Machine learning model
    # ------------------------------------------------------------------
    def _ensure_model(self) -> None:
        if not self._sklearn_available:
            return

        samples = self._load_dataset()
        if samples.empty or len(samples) < self.MIN_SAMPLES_FOR_MODEL:
            self._model = None
            self._model_sample_size = len(samples)
            return

        features = samples[[
            'origin_code',
            'destination_code',
            'assignment_type',
            'hour',
            'weekday',
            'month',
            'estimated_minutes',
            'route_minutes',
            'unloading_minutes',
        ]]
        target = samples['target_minutes']

        categorical_features = ['origin_code', 'destination_code', 'assignment_type']
        numeric_features = ['hour', 'weekday', 'month', 'estimated_minutes', 'route_minutes', 'unloading_minutes']

        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
                ('num', StandardScaler(), numeric_features),
            ]
        )

        model = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', SGDRegressor(max_iter=500, tol=1e-3, penalty='l2', learning_rate='optimal')),
        ])

        model.fit(features, target)
        self._model = model
        self._model_sample_size = len(samples)

    def _predict_with_model(
        self,
        origin: Location,
        destination: Location,
        assignment_type: str,
        scheduled_datetime,
        base_estimate: Optional[int],
    ) -> Optional[float]:
        if not self._sklearn_available:
            return None

        self._ensure_model()
        if self._model is None:
            return None

        scheduled = scheduled_datetime.astimezone(timezone.get_current_timezone())
        features = pd.DataFrame.from_records([
            {
                'origin_code': origin.code,
                'destination_code': destination.code,
                'assignment_type': assignment_type,
                'hour': scheduled.hour,
                'weekday': scheduled.weekday(),
                'month': scheduled.month,
                'estimated_minutes': base_estimate or DEFAULT_FALLBACK_MINUTES,
                'route_minutes': 0.0,
                'unloading_minutes': 0.0,
            }
        ])

        prediction = self._model.predict(features)[0]
        return float(prediction)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def predict(
        self,
        *,
        origin: Optional[Location],
        destination: Optional[Location],
        assignment_type: str,
        scheduled_datetime,
    ) -> PredictionResult:
        if origin is None or destination is None:
            return PredictionResult(minutes=DEFAULT_FALLBACK_MINUTES, source='default', sample_size=0)

        assignment_type = assignment_type or 'ENTREGA'
        scheduled_datetime = scheduled_datetime or timezone.now()

        historical_avg, historical_count = self._historical_route_average(origin, destination, assignment_type)
        matrix_minutes = self._time_matrix_estimate(origin, destination)
        model_minutes = self._predict_with_model(
            origin,
            destination,
            assignment_type,
            scheduled_datetime,
            matrix_minutes,
        )

        if model_minutes is not None:
            if model_minutes <= 0 or model_minutes > 720:
                model_minutes = None

        estimates: list[tuple[str, float, int]] = []
        if model_minutes and model_minutes > 0:
            estimates.append(('ml', model_minutes, self._model_sample_size))
        if historical_avg and historical_avg > 0:
            estimates.append(('historical', historical_avg, historical_count))
        if matrix_minutes and matrix_minutes > 0:
            estimates.append(('matrix', matrix_minutes, historical_count))

        if not estimates:
            return PredictionResult(minutes=DEFAULT_FALLBACK_MINUTES, source='default', sample_size=0)

        # Promedio ponderado favorenciendo el modelo si está disponible
        weights = {
            'ml': 0.6,
            'historical': 0.3,
            'matrix': 0.2,
        }

        total_weight = 0.0
        weighted_sum = 0.0
        sample_size = 0
        for source, minutes, count in estimates:
            weight = weights.get(source, 0.1)
            weighted_sum += minutes * weight
            total_weight += weight
            sample_size = max(sample_size, count)

        final_minutes = weighted_sum / total_weight if total_weight else DEFAULT_FALLBACK_MINUTES
        final_minutes = max(int(round(final_minutes)), 30)
        primary_source = estimates[0][0]

        return PredictionResult(minutes=final_minutes, source=primary_source, sample_size=sample_size)