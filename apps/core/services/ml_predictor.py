"""
Servicio de predicción de tiempos usando Machine Learning

Integra modelos ML (TiempoOperacion, TiempoViaje) con Mapbox
para predicciones más precisas basadas en datos históricos.
"""
from decimal import Decimal
from datetime import datetime
from apps.programaciones.models import TiempoOperacion, TiempoViaje
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
            logger.warning(f"Error obteniendo tiempo ML: {str(e)}. Usando default.")
            
            # Fallback a tiempo default del CD
            if tipo_operacion == 'descarga_cd' and cd.tiempo_promedio_descarga_min:
                return cd.tiempo_promedio_descarga_min
            
            # Default genérico
            return 60
    
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
            mapbox_resultado = MapboxService.calcular_ruta(
                origen_coords[0], origen_coords[1],
                destino_coords[0], destino_coords[1]
            )
            
            if not mapbox_resultado or 'duration_minutes' not in mapbox_resultado:
                logger.error("Mapbox no devolvió tiempo válido")
                return {
                    'tiempo_estimado_min': 60,  # Default
                    'distancia_km': 0,
                    'fuente': 'default',
                    'tiempo_mapbox_min': 0
                }
            
            tiempo_mapbox = int(mapbox_resultado['duration_minutes'])
            distancia_km = mapbox_resultado.get('distance_km', 0)
            
            # 2. Intentar ajustar con ML
            try:
                tiempo_ml = TiempoViaje.obtener_tiempo_aprendido(
                    origen_coords=origen_coords,
                    destino_coords=destino_coords,
                    tiempo_mapbox=tiempo_mapbox,
                    hora_salida=hora_salida or datetime.now(),
                    conductor=conductor
                )
                
                # Si ML devolvió algo diferente, usarlo
                if tiempo_ml != tiempo_mapbox:
                    factor = tiempo_ml / tiempo_mapbox if tiempo_mapbox > 0 else 1.0
                    logger.debug(f"Tiempo ajustado por ML: {tiempo_mapbox}min → {tiempo_ml}min (factor {factor:.2f}x)")
                    
                    return {
                        'tiempo_estimado_min': tiempo_ml,
                        'distancia_km': distancia_km,
                        'fuente': 'ml',
                        'tiempo_mapbox_min': tiempo_mapbox,
                        'factor_correccion': round(factor, 2)
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
            return {
                'tiempo_estimado_min': 60,
                'distancia_km': 0,
                'fuente': 'error',
                'tiempo_mapbox_min': 0,
                'error': str(e)
            }
    
    @classmethod
    def calcular_ocupacion_conductor(cls, driver, nueva_programacion):
        """
        Calcula ocupación total del conductor si se le asigna nueva programación
        
        Usa ML para predicciones más precisas:
        - Tiempo de viaje ajustado por tráfico histórico
        - Tiempo de operación ajustado por CD y tipo
        
        Args:
            driver: Driver object
            nueva_programacion: Programacion object
        
        Returns:
            dict: {
                'tiempo_total_min': int,
                'porcentaje_jornada': float,
                'desglose': {
                    'viajes': int,
                    'operaciones': int,
                    'esperas': int
                }
            }
        """
        try:
            cd = nueva_programacion.cd
            container = nueva_programacion.container
            
            # 1. Tiempo de viaje (origen → CD)
            # Asumimos origen = última posición del conductor o CCTI
            if driver.ultima_posicion_lat and driver.ultima_posicion_lng:
                origen_coords = (driver.ultima_posicion_lat, driver.ultima_posicion_lng)
            elif container.ccti_actual:
                origen_coords = (container.ccti_actual.lat, container.ccti_actual.lng)
            else:
                # Sin origen conocido, usar estimación conservadora
                tiempo_viaje = 60  # 1 hora default
            
            if 'origen_coords' in locals():
                destino_coords = (cd.lat, cd.lng)
                prediccion_viaje = cls.predecir_tiempo_viaje(
                    origen_coords=origen_coords,
                    destino_coords=destino_coords,
                    hora_salida=nueva_programacion.fecha_programada,
                    conductor=driver
                )
                tiempo_viaje = prediccion_viaje['tiempo_estimado_min']
            
            # 2. Tiempo de operación (descarga en CD)
            if cd.requiere_espera_carga:
                # CD requiere que conductor espere descarga
                tipo_operacion = 'descarga_cd'
                tiempo_operacion = cls.predecir_tiempo_operacion(
                    cd=cd,
                    tipo_operacion=tipo_operacion,
                    conductor=driver
                )
            else:
                # Drop and hook - conductor no espera
                tiempo_operacion = 15  # Solo tiempo de soltar contenedor
            
            # 3. Tiempo de retorno (opcional - si necesita volver a base)
            # Por ahora no lo incluimos, pero se puede agregar
            tiempo_retorno = 0
            
            # Total
            tiempo_total = tiempo_viaje + tiempo_operacion + tiempo_retorno
            
            # Calcular porcentaje de jornada (asumiendo 10 horas = 600 min)
            jornada_min = 600
            porcentaje = (tiempo_total / jornada_min) * 100
            
            return {
                'tiempo_total_min': tiempo_total,
                'porcentaje_jornada': round(porcentaje, 1),
                'desglose': {
                    'viaje': tiempo_viaje,
                    'operacion': tiempo_operacion,
                    'retorno': tiempo_retorno
                }
            }
        
        except Exception as e:
            logger.error(f"Error calculando ocupación ML: {str(e)}")
            # Fallback a estimación conservadora
            return {
                'tiempo_total_min': 120,  # 2 horas default
                'porcentaje_jornada': 20.0,
                'desglose': {
                    'viaje': 60,
                    'operacion': 60,
                    'retorno': 0
                },
                'error': str(e)
            }
    
    @classmethod
    def calcular_eta_entrega(cls, driver, programacion):
        """
        Calcula ETA (Estimated Time of Arrival) de entrega
        
        Returns:
            datetime: Hora estimada de entrega
        """
        try:
            ocupacion = cls.calcular_ocupacion_conductor(driver, programacion)
            tiempo_total = ocupacion['tiempo_total_min']
            
            # Si hay fecha programada, partir desde ahí
            if programacion.fecha_programada:
                from datetime import timedelta
                eta = programacion.fecha_programada + timedelta(minutes=tiempo_total)
                return eta
            
            # Si no, desde ahora
            from datetime import datetime, timedelta
            eta = datetime.now() + timedelta(minutes=tiempo_total)
            return eta
        
        except Exception as e:
            logger.error(f"Error calculando ETA: {str(e)}")
            return None
