"""
Servicio de asignación automática de conductores
Implementa algoritmo con scores ponderados + Machine Learning
"""
from decimal import Decimal
from django.conf import settings
from apps.drivers.models import Driver
from apps.programaciones.models import Programacion
from apps.core.services.mapbox import MapboxService
from apps.core.services.ml_predictor import MLTimePredictor
import logging

logger = logging.getLogger(__name__)


class AssignmentService:
    """
    Servicio de asignación automática de conductores a programaciones
    
    Criterios de asignación (configurable via settings):
    - Disponibilidad (30%): ¿Está presente y tiene capacidad?
    - Ocupación (25%): ¿Cuántas entregas ya tiene?
    - Cumplimiento (30%): Historial de cumplimiento
    - Proximidad (15%): Distancia al CD de entrega
    """
    
    # Pesos por defecto (pueden venir de settings)
    PESO_DISPONIBILIDAD = Decimal(str(getattr(settings, 'ASSIGNMENT_WEIGHT_DISPONIBILIDAD', 0.30)))
    PESO_OCUPACION = Decimal(str(getattr(settings, 'ASSIGNMENT_WEIGHT_OCUPACION', 0.25)))
    PESO_CUMPLIMIENTO = Decimal(str(getattr(settings, 'ASSIGNMENT_WEIGHT_CUMPLIMIENTO', 0.30)))
    PESO_PROXIMIDAD = Decimal(str(getattr(settings, 'ASSIGNMENT_WEIGHT_PROXIMIDAD', 0.15)))
    
    @classmethod
    def calcular_score_disponibilidad(cls, driver):
        """
        Score basado en si el conductor está disponible
        100 = Disponible
        0 = No disponible
        """
        if driver.esta_disponible:
            return Decimal('100.0')
        return Decimal('0.0')
    
    @classmethod
    def calcular_score_ocupacion(cls, driver, programacion=None):
        """
        Score inversamente proporcional a la ocupación
        100 = Sin entregas (0% ocupado)
        0 = Completamente ocupado (100%)
        
        Si se proporciona programacion, usa ML para calcular ocupación futura
        """
        if programacion:
            # Usar ML para predicción más precisa
            try:
                ocupacion_data = MLTimePredictor.calcular_ocupacion_conductor(driver, programacion)
                porcentaje_ocupacion = Decimal(str(ocupacion_data['porcentaje_jornada']))
                
                # Limitar a 100%
                if porcentaje_ocupacion > 100:
                    porcentaje_ocupacion = Decimal('100.0')
                
                logger.debug(f"Ocupación ML para {driver.nombre}: {porcentaje_ocupacion}%")
                return Decimal('100.0') - porcentaje_ocupacion
            
            except Exception as e:
                logger.warning(f"Error calculando ocupación ML: {str(e)}. Usando fallback.")
        
        # Fallback a método original
        ocupacion = driver.ocupacion_porcentaje
        return Decimal('100.0') - ocupacion
    
    @classmethod
    def calcular_score_cumplimiento(cls, driver):
        """
        Score basado en el historial de cumplimiento
        Directamente el porcentaje de cumplimiento
        """
        return driver.cumplimiento_porcentaje
    
    @classmethod
    def calcular_score_proximidad(cls, driver, cd):
        """
        Score basado en la distancia del conductor al CD
        Usa Mapbox para calcular distancia real
        """
        # Si el conductor no tiene posición conocida, score medio
        if not driver.ultima_posicion_lat or not driver.ultima_posicion_lng:
            return Decimal('50.0')
        
        # Si el CD no tiene coordenadas, score medio
        if not cd.lat or not cd.lng:
            return Decimal('50.0')
        
        # Calcular distancia con Mapbox
        score = MapboxService.calcular_score_proximidad(
            float(driver.ultima_posicion_lat),
            float(driver.ultima_posicion_lng),
            float(cd.lat),
            float(cd.lng)
        )
        
        return Decimal(str(score))
    
    @classmethod
    def calcular_score_total(cls, driver, programacion):
        """
        Calcula el score total ponderado para un conductor
        
        Usa Machine Learning para ocupación más precisa
        
        Returns:
            dict: {
                'score_total': Decimal,
                'desglose': {
                    'disponibilidad': Decimal,
                    'ocupacion': Decimal,
                    'cumplimiento': Decimal,
                    'proximidad': Decimal
                },
                'tiempo_estimado_min': int (opcional, con ML),
                'distancia_km': float (opcional)
            }
        """
        # Calcular scores individuales (ocupación ahora usa ML)
        score_disponibilidad = cls.calcular_score_disponibilidad(driver)
        score_ocupacion = cls.calcular_score_ocupacion(driver, programacion)  # ← Con ML
        score_cumplimiento = cls.calcular_score_cumplimiento(driver)
        score_proximidad = cls.calcular_score_proximidad(driver, programacion.cd)
        
        # Si no está disponible, score total = 0
        if score_disponibilidad == 0:
            return {
                'score_total': Decimal('0.0'),
                'desglose': {
                    'disponibilidad': Decimal('0.0'),
                    'ocupacion': Decimal('0.0'),
                    'cumplimiento': Decimal('0.0'),
                    'proximidad': Decimal('0.0')
                }
            }
        
        # Calcular score total ponderado
        score_total = (
            (score_disponibilidad * cls.PESO_DISPONIBILIDAD) +
            (score_ocupacion * cls.PESO_OCUPACION) +
            (score_cumplimiento * cls.PESO_CUMPLIMIENTO) +
            (score_proximidad * cls.PESO_PROXIMIDAD)
        )
        
        return {
            'score_total': round(score_total, 2),
            'desglose': {
                'disponibilidad': round(score_disponibilidad, 2),
                'ocupacion': round(score_ocupacion, 2),
                'cumplimiento': round(score_cumplimiento, 2),
                'proximidad': round(score_proximidad, 2)
            }
        }
    
    @classmethod
    def obtener_conductores_disponibles_con_score(cls, programacion):
        """
        Obtiene todos los conductores disponibles ordenados por score
        
        Returns:
            list: Lista de dicts con {
                'driver': Driver,
                'score': Decimal,
                'desglose': dict
            }
        """
        # Obtener conductores activos y presentes
        drivers = Driver.objects.filter(activo=True, presente=True)
        
        resultados = []
        
        for driver in drivers:
            score_data = cls.calcular_score_total(driver, programacion)
            
            # Solo incluir si tiene score > 0 (está disponible)
            if score_data['score_total'] > 0:
                resultados.append({
                    'driver': driver,
                    'score': score_data['score_total'],
                    'desglose': score_data['desglose']
                })
        
        # Ordenar por score descendente
        resultados.sort(key=lambda x: x['score'], reverse=True)
        
        return resultados
    
    @classmethod
    def asignar_mejor_conductor(cls, programacion, usuario=None):
        """
        Asigna automáticamente el mejor conductor disponible a una programación
        
        Returns:
            dict: {
                'success': bool,
                'driver': Driver (si success=True),
                'score': Decimal (si success=True),
                'desglose': dict (si success=True),
                'error': str (si success=False)
            }
        """
        try:
            # Verificar que la programación no tenga conductor ya
            if programacion.driver:
                return {
                    'success': False,
                    'error': f'La programación ya tiene conductor asignado: {programacion.driver.nombre}'
                }
            
            # Obtener conductores con scores
            conductores = cls.obtener_conductores_disponibles_con_score(programacion)
            
            if not conductores:
                return {
                    'success': False,
                    'error': 'No hay conductores disponibles'
                }
            
            # Seleccionar el mejor (primero de la lista ordenada)
            mejor = conductores[0]
            driver = mejor['driver']
            
            # Asignar
            programacion.asignar_conductor(driver, usuario)
            
            logger.info(f"Conductor {driver.nombre} asignado a {programacion.container.container_id} con score {mejor['score']}")
            
            return {
                'success': True,
                'driver': driver,
                'score': mejor['score'],
                'desglose': mejor['desglose']
            }
        
        except Exception as e:
            logger.error(f"Error en asignación automática: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def asignar_multiples(cls, programaciones, usuario=None):
        """
        Asigna conductores a múltiples programaciones
        
        Returns:
            dict: {
                'asignadas': int,
                'fallidas': int,
                'detalles': list
            }
        """
        resultados = {
            'asignadas': 0,
            'fallidas': 0,
            'detalles': []
        }
        
        for programacion in programaciones:
            resultado = cls.asignar_mejor_conductor(programacion, usuario)
            
            if resultado['success']:
                resultados['asignadas'] += 1
                resultados['detalles'].append({
                    'programacion_id': programacion.id,
                    'container_id': programacion.container.container_id,
                    'driver': resultado['driver'].nombre,
                    'score': float(resultado['score']),
                    'success': True
                })
            else:
                resultados['fallidas'] += 1
                resultados['detalles'].append({
                    'programacion_id': programacion.id,
                    'container_id': programacion.container.container_id,
                    'error': resultado['error'],
                    'success': False
                })
        
        return resultados
