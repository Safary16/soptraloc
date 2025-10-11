"""
Servicio de Machine Learning para predicción de tiempos.
Aprende de los registros reales y actualiza las predicciones.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

from django.db.models import Avg, Count, Q, StdDev
from django.utils import timezone

from apps.routing.models import (
    LocationPair,
    OperationTime,
    ActualTripRecord,
    ActualOperationRecord
)

logger = logging.getLogger(__name__)


class TimePredictionML:
    """
    Sistema de Machine Learning simple para predicción de tiempos.
    Versión 1.0: Usa promedios ponderados y regresión simple.
    Versión futura: Modelos más sofisticados (RandomForest, XGBoost).
    """
    
    # Pesos para promedios ponderados
    RECENT_DATA_WEIGHT = 0.6  # 60% para datos recientes
    HISTORICAL_DATA_WEIGHT = 0.4  # 40% para datos históricos
    
    # Umbral mínimo de datos para confiar en ML
    MIN_SAMPLES_FOR_ML = 5
    
    # Días para considerar "reciente"
    RECENT_DAYS = 30
    
    @classmethod
    def update_all_predictions(cls):
        """
        Actualiza todas las predicciones ML.
        Ejecutar periódicamente (ej: diario con cron/celery).
        """
        logger.info("🤖 Iniciando actualización de predicciones ML...")
        
        # Actualizar pares de ubicaciones
        location_pairs_updated = cls.update_location_pairs()
        
        # Actualizar operaciones
        operations_updated = cls.update_operation_times()
        
        logger.info(
            f"✅ ML actualizado: {location_pairs_updated} rutas, "
            f"{operations_updated} operaciones"
        )
        
        return {
            'location_pairs': location_pairs_updated,
            'operations': operations_updated,
            'timestamp': timezone.now()
        }
    
    @classmethod
    def update_location_pairs(cls) -> int:
        """
        Actualiza predicciones ML para todos los pares de ubicaciones.
        """
        updated_count = 0
        
        for pair in LocationPair.objects.filter(is_active=True):
            updated = cls._update_single_location_pair(pair)
            if updated:
                updated_count += 1
        
        return updated_count
    
    @classmethod
    def _update_single_location_pair(cls, pair: LocationPair) -> bool:
        """
        Actualiza predicción ML para un par específico.
        
        Returns:
            bool: True si se actualizó, False si no había suficientes datos
        """
        # Obtener registros reales de viajes
        all_trips = ActualTripRecord.objects.filter(
            origin=pair.origin,
            destination=pair.destination,
            is_active=True
        )
        
        total_count = all_trips.count()
        
        # Verificar si hay suficientes datos
        if total_count < cls.MIN_SAMPLES_FOR_ML:
            logger.debug(
                f"⏭️  Insuficientes datos para {pair} "
                f"({total_count}/{cls.MIN_SAMPLES_FOR_ML})"
            )
            return False
        
        # Separar datos recientes vs históricos
        recent_cutoff = timezone.now() - timedelta(days=cls.RECENT_DAYS)
        
        recent_trips = all_trips.filter(departure_time__gte=recent_cutoff)
        historical_trips = all_trips.filter(departure_time__lt=recent_cutoff)
        
        # Calcular promedios
        recent_avg = recent_trips.aggregate(
            avg=Avg('duration_minutes')
        )['avg'] or 0
        
        historical_avg = historical_trips.aggregate(
            avg=Avg('duration_minutes')
        )['avg'] or 0
        
        # Si no hay datos recientes, usar solo históricos
        if recent_trips.count() == 0:
            predicted_time = int(historical_avg) if historical_avg else pair.base_travel_time
            confidence = 50.0
        else:
            # Promedio ponderado
            predicted_time = int(
                (recent_avg * cls.RECENT_DATA_WEIGHT) +
                (historical_avg * cls.HISTORICAL_DATA_WEIGHT)
            )
            
            # Calcular confianza basada en cantidad y variabilidad
            std_dev = recent_trips.aggregate(
                std=StdDev('duration_minutes')
            )['std'] or 0
            
            # Confianza: más datos y menos variabilidad = mayor confianza
            sample_confidence = min(100, (total_count / 50) * 100)
            variability_confidence = max(0, 100 - (std_dev / predicted_time * 100 if predicted_time > 0 else 0))
            confidence = (sample_confidence + variability_confidence) / 2
        
        # Actualizar modelo
        pair.ml_predicted_time = predicted_time
        pair.ml_confidence = Decimal(str(round(confidence, 2)))
        pair.ml_last_update = timezone.now()
        pair.total_trips = total_count
        pair.avg_actual_time = Decimal(str(round(
            all_trips.aggregate(avg=Avg('duration_minutes'))['avg'] or 0,
            2
        )))
        pair.save()
        
        logger.info(
            f"✅ {pair}: Predicción={predicted_time} min, "
            f"Confianza={confidence:.1f}%, Muestras={total_count}"
        )
        
        return True
    
    @classmethod
    def update_operation_times(cls) -> int:
        """
        Actualiza predicciones ML para tiempos de operaciones.
        """
        updated_count = 0
        
        for op_time in OperationTime.objects.filter(is_active=True):
            updated = cls._update_single_operation(op_time)
            if updated:
                updated_count += 1
        
        return updated_count
    
    @classmethod
    def _update_single_operation(cls, op_time: OperationTime) -> bool:
        """
        Actualiza predicción ML para una operación específica.
        """
        # Obtener registros reales
        records = ActualOperationRecord.objects.filter(
            location=op_time.location,
            operation_type=op_time.operation_type,
            is_active=True,
            had_issues=False  # Excluir operaciones con problemas
        )
        
        total_count = records.count()
        
        if total_count < cls.MIN_SAMPLES_FOR_ML:
            return False
        
        # Datos recientes vs históricos
        recent_cutoff = timezone.now() - timedelta(days=cls.RECENT_DAYS)
        
        recent_records = records.filter(start_time__gte=recent_cutoff)
        
        recent_avg = recent_records.aggregate(
            avg=Avg('duration_minutes')
        )['avg'] or 0
        
        historical_avg = records.filter(start_time__lt=recent_cutoff).aggregate(
            avg=Avg('duration_minutes')
        )['avg'] or 0
        
        # Calcular predicción
        if recent_records.count() == 0:
            predicted_time = int(historical_avg) if historical_avg else op_time.avg_time
            confidence = 50.0
        else:
            predicted_time = int(
                (recent_avg * cls.RECENT_DATA_WEIGHT) +
                (historical_avg * cls.HISTORICAL_DATA_WEIGHT)
            )
            
            # Confianza
            std_dev = recent_records.aggregate(
                std=StdDev('duration_minutes')
            )['std'] or 0
            
            sample_confidence = min(100, (total_count / 30) * 100)
            variability_confidence = max(0, 100 - (std_dev / predicted_time * 100 if predicted_time > 0 else 0))
            confidence = (sample_confidence + variability_confidence) / 2
        
        # Actualizar
        op_time.ml_predicted_time = predicted_time
        op_time.ml_confidence = Decimal(str(round(confidence, 2)))
        op_time.ml_last_update = timezone.now()
        op_time.total_operations = total_count
        op_time.save()
        
        logger.info(
            f"✅ {op_time}: Predicción={predicted_time} min, "
            f"Confianza={confidence:.1f}%, Muestras={total_count}"
        )
        
        return True
    
    @classmethod
    def get_prediction_for_route(
        cls,
        origin_id: int,
        destination_id: int,
        departure_time: Optional[datetime] = None
    ) -> Dict:
        """
        Obtiene predicción de tiempo para un trayecto específico.
        
        Args:
            origin_id: ID de ubicación origen
            destination_id: ID de ubicación destino
            departure_time: Hora de salida (opcional)
        
        Returns:
            Dict con tiempo_estimado, confianza, fuente
        """
        try:
            pair = LocationPair.objects.get(
                origin_id=origin_id,
                destination_id=destination_id,
                is_active=True
            )
            
            estimated_time = pair.get_estimated_time(departure_time)
            
            # Determinar fuente de la predicción
            if pair.ml_predicted_time and pair.ml_confidence and pair.ml_confidence > 70:
                source = 'ml'
                confidence = float(pair.ml_confidence)
            else:
                source = 'manual'
                confidence = 60.0
            
            return {
                'estimated_time': estimated_time,
                'confidence': confidence,
                'source': source,
                'total_samples': pair.total_trips,
                'last_ml_update': pair.ml_last_update,
                'base_time': pair.base_travel_time,
                'ml_time': pair.ml_predicted_time,
            }
            
        except LocationPair.DoesNotExist:
            return {
                'estimated_time': None,
                'confidence': 0,
                'source': 'none',
                'error': 'No se encontró ruta configurada entre estas ubicaciones'
            }
    
    @classmethod
    def analyze_prediction_accuracy(cls) -> Dict:
        """
        Analiza la precisión de las predicciones vs tiempos reales.
        Útil para monitorear calidad del modelo.
        """
        # Comparar últimos 30 días
        recent_cutoff = timezone.now() - timedelta(days=30)
        
        recent_trips = ActualTripRecord.objects.filter(
            departure_time__gte=recent_cutoff,
            is_active=True
        )
        
        results = []
        total_error = 0
        count = 0
        
        for trip in recent_trips:
            try:
                pair = LocationPair.objects.get(
                    origin=trip.origin,
                    destination=trip.destination
                )
                
                predicted = pair.get_estimated_time(trip.departure_time)
                actual = trip.duration_minutes
                error = abs(predicted - actual)
                error_pct = (error / actual * 100) if actual > 0 else 0
                
                results.append({
                    'origin': trip.origin.name,
                    'destination': trip.destination.name,
                    'predicted': predicted,
                    'actual': actual,
                    'error_minutes': error,
                    'error_percent': round(error_pct, 1)
                })
                
                total_error += error
                count += 1
                
            except LocationPair.DoesNotExist:
                continue
        
        avg_error = total_error / count if count > 0 else 0
        
        return {
            'total_predictions': count,
            'avg_error_minutes': round(avg_error, 1),
            'accuracy_rate': round(100 - (avg_error / 60 * 100), 1),  # Asumiendo 60 min promedio
            'recent_comparisons': results[:10],  # Top 10
            'analysis_period_days': 30,
        }
    
    @classmethod
    def suggest_route_optimizations(cls) -> List[Dict]:
        """
        Sugiere optimizaciones basadas en datos históricos.
        Ej: Rutas que consistentemente tardan más de lo esperado.
        """
        suggestions = []
        
        # Rutas con alta variabilidad
        for pair in LocationPair.objects.filter(is_active=True, total_trips__gte=10):
            trips = ActualTripRecord.objects.filter(
                origin=pair.origin,
                destination=pair.destination
            )
            
            stats = trips.aggregate(
                avg=Avg('duration_minutes'),
                std=StdDev('duration_minutes')
            )
            
            if stats['std'] and stats['avg']:
                variability = (stats['std'] / stats['avg']) * 100
                
                if variability > 30:  # Más de 30% de variabilidad
                    suggestions.append({
                        'route': str(pair),
                        'issue': 'high_variability',
                        'description': f'Variabilidad alta ({variability:.1f}%)',
                        'suggestion': 'Revisar factores externos (tráfico, horarios)',
                        'avg_time': int(stats['avg']),
                        'std_dev': int(stats['std'])
                    })
        
        # Rutas donde ML difiere mucho del base
        for pair in LocationPair.objects.filter(
            is_active=True,
            ml_predicted_time__isnull=False
        ):
            diff = abs(pair.ml_predicted_time - pair.base_travel_time)
            diff_pct = (diff / pair.base_travel_time * 100) if pair.base_travel_time > 0 else 0
            
            if diff_pct > 20:  # Más de 20% de diferencia
                suggestions.append({
                    'route': str(pair),
                    'issue': 'base_time_outdated',
                    'description': f'Tiempo base desactualizado ({diff_pct:.1f}% diferencia)',
                    'suggestion': f'Actualizar tiempo base de {pair.base_travel_time} a {pair.ml_predicted_time} minutos',
                    'base_time': pair.base_travel_time,
                    'ml_time': pair.ml_predicted_time
                })
        
        return suggestions


class RouteOptimizer:
    """
    Optimizador de rutas usando los tiempos predichos por ML.
    Versión simple: Clustering geográfico + orden por proximidad.
    """
    
    @classmethod
    def optimize_daily_routes(cls, date, driver_ids=None):
        """
        Optimiza rutas para un día específico.
        
        Args:
            date: Fecha a optimizar
            driver_ids: Lista de IDs de conductores (opcional)
        
        Returns:
            Dict con rutas optimizadas
        """
        # TODO: Implementar algoritmo VRP
        # Por ahora, retornar placeholder
        return {
            'status': 'pending_implementation',
            'message': 'Optimización de rutas en desarrollo'
        }
    
    @classmethod
    def suggest_container_grouping(cls, container_ids: List[int]) -> Dict:
        """
        Sugiere cómo agrupar contenedores en rutas.
        Basado en ubicaciones y tiempos.
        """
        # TODO: Implementar clustering
        return {
            'status': 'pending_implementation',
            'message': 'Agrupación de contenedores en desarrollo'
        }
