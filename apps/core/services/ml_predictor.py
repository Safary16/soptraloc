"""
Servicio de predicción de tiempos usando Machine Learning

Integra modelos ML (TiempoOperacion, TiempoViaje) con Mapbox
para predicciones más precisas basadas en datos históricos.
"""
from datetime import datetime
from apps.programaciones.models import TiempoOperacion
from apps.core.services.mapbox import MapboxService
import logging

logger = logging.getLogger(__name__)


class MLTimePredictor:
    """
    Predictor de tiempos usando Machine Learning
    
    Combina:
    - Datos históricos de TiempoOperacion (carga/descarga)
    - Datos históricos de TiempoViaje (tráfico real)
    - Fallback a Mapbox si no hay suficientes datos
    """
    
    @classmethod
    def predecir_tiempo_operacion(cls, cd, tipo_operacion='descarga_cd', conductor=None):
        """
        Predice tiempo de operación en CD usando ML
        
        Args:
            cd: CD object
            tipo_operacion: str ('carga_ccti', 'descarga_cd', 'retiro_puerto', 'devolucion_vacio')
            conductor: Driver object (opcional)
        
        Returns:
            int: Tiempo estimado en minutos
        """
        try:
            # Intentar obtener tiempo aprendido
            tiempo_ml = TiempoOperacion.obtener_tiempo_aprendido(
                cd=cd,
                tipo_operacion=tipo_operacion,
                conductor=conductor
            )

            logger.debug(f"Tiempo ML para {cd.nombre} ({tipo_operacion}): {tiempo_ml} min")
            return tiempo_ml

        except Exception as e:
            logger.warning(f"Error obteniendo tiempo ML: {str(e)}. Sin default ficticio.")

            # Antes: retornabamos 60 ficticio, contaminando los cálculos aguas abajo.
            # Ahora: retornamos None y marcamos requires_attention=True para que las
            # vistas (anomaly_detector.ETAEstimator, programaciones/views) decidan
            # como manejar el caso (mostrar advertencia al operador vs asignar ciegamente).
            try:
                if tipo_operacion == 'descarga_cd' and getattr(cd, 'tiempo_promedio_descarga_min', None):
                    # Si tenemos un dato específico del CD, devolvemos ese con flag
                    # (no es ficticio, es metadata operativa del CD).
                    return cd.tiempo_promedio_descarga_min
            except Exception:
                pass
            return None
    
    @classmethod
    def predecir_tiempo_viaje(cls, origen_coords, destino_coords, hora_salida=None, conductor=None):
        """
        Predice tiempo de viaje usando ML + Mapbox
        
        Estrategia:
        1. Obtener tiempo base de Mapbox
        2. Ajustar con factor aprendido de ML
        3. Si no hay datos ML, usar Mapbox directo
        
        Args:
            origen_coords: tuple (lat, lon)
            destino_coords: tuple (lat, lon)
            hora_salida: datetime opcional
            conductor: Driver opcional
        
        Returns:
            dict: {
                'tiempo_estimado_min': int,
                'distancia_km': float,
                'fuente': str ('ml' o 'mapbox'),
                'tiempo_mapbox_min': int (original),
                'factor_correccion': float (si ML)
            }
        """
        try:
            # 1. Obtener tiempo base de Mapbox
            origen_lat, origen_lng = float(origen_coords[0]), float(origen_coords[1])
            destino_lat, destino_lng = float(destino_coords[0]), float(destino_coords[1])

            mapbox_resultado = MapboxService.calcular_ruta(
                origen_lng, origen_lat,
                destino_lng, destino_lat
            )

            if not mapbox_resultado or 'duration_minutes' not in mapbox_resultado:
                logger.error("Mapbox no devolvió tiempo válido")
                # Antes: tiempo_estimado_min=60 ficticio. Ahora: None + requires_attention
                # para que el operador vea la advertencia en lugar de un ETA inventado.
                return {
                    'tiempo_estimado_min': None,
                    'distancia_km': None,
                    'fuente': 'error',
                    'tiempo_mapbox_min': None,
                    'requires_attention': True,
                    'error': 'mapbox_sin_tiempo_valido',
                }
            
            tiempo_mapbox = int(mapbox_resultado['duration_minutes'])
            distancia_km = mapbox_resultado.get('distance_km', 0)
            
            # 2. Ajustar con el motor ÚNICO de aprendizaje (OperationalLearningEngine):
            #    mezcla Mapbox + histórico por ruta/hora/día/conductor.
            from apps.core.services.learning_engine import OperationalLearningEngine
            try:
                base_route = {
                    'duration_minutes': tiempo_mapbox,
                    'distance_km': distancia_km,
                    'route_signature': None,
                }
                prediccion = OperationalLearningEngine.predict_route(
                    origin=origen_coords,
                    destination=destino_coords,
                    departure=hora_salida or datetime.now(),
                    base_route=base_route,
                    driver=conductor,
                )
                tiempo_ml = prediccion['predicted_minutes']
                
                # Si ML devolvió algo diferente, usarlo
                if tiempo_ml != tiempo_mapbox and tiempo_ml > 0:
                    factor = tiempo_ml / tiempo_mapbox if tiempo_mapbox > 0 else 1.0
                    logger.debug(f"Tiempo ajustado por ML: {tiempo_mapbox}min → {tiempo_ml}min (factor {factor:.2f}x)")
                    
                    return {
                        'tiempo_estimado_min': tiempo_ml,
                        'distancia_km': distancia_km,
                        'fuente': 'ml',
                        'tiempo_mapbox_min': tiempo_mapbox,
                        'factor_correccion': round(factor, 2),
                    }
            
            except Exception as e:
                logger.debug(f"Sin datos ML suficientes: {str(e)}. Usando Mapbox directo.")
            
            # 3. Fallback a Mapbox directo
            return {
                'tiempo_estimado_min': tiempo_mapbox,
                'distancia_km': distancia_km,
                'fuente': 'mapbox',
                'tiempo_mapbox_min': tiempo_mapbox
            }
        
        except Exception as e:
            logger.error(f"Error prediciendo tiempo de viaje: {str(e)}")
            # Antes: tiempo_estimado_min=60 ficticio. Ahora: None + requires_attention
            # para que la vista muestre advertencia y NO asigne ETA falsa.
            return {
                'tiempo_estimado_min': None,
                'distancia_km': None,
                'fuente': 'error',
                'tiempo_mapbox_min': None,
                'requires_attention': True,
                'error': str(e),
            }
    
    
