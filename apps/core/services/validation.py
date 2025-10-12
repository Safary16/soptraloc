"""
Servicio de validación de pre-asignación con cálculos de tiempo
Previene conflictos de doble asignación usando tiempos reales de Mapbox
"""
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
import logging

from apps.core.services.mapbox import MapboxService
from apps.programaciones.models import Programacion

logger = logging.getLogger(__name__)


class PreAssignmentValidationService:
    """
    Validación de asignaciones considerando ventanas de tiempo reales
    """
    
    @classmethod
    def validar_disponibilidad_temporal(cls, driver, programacion_nueva, buffer_minutos=30):
        """
        Valida si el conductor está disponible en la ventana de tiempo requerida
        
        Args:
            driver: Conductor a validar
            programacion_nueva: Programación que se desea asignar
            buffer_minutos: Tiempo de buffer entre entregas (default 30 min)
        
        Returns:
            dict: {
                'disponible': bool,
                'conflictos': list,
                'tiempo_requerido': int (minutos),
                'ventana_ocupada': dict o None
            }
        """
        if not driver.esta_disponible:
            return {
                'disponible': False,
                'conflictos': ['Conductor no disponible (presente=False o asignaciones completas)'],
                'tiempo_requerido': 0,
                'ventana_ocupada': None
            }
        
        # Calcular tiempo requerido para la nueva asignación
        tiempo_requerido = cls._calcular_tiempo_total_asignacion(programacion_nueva)
        
        # Obtener todas las programaciones activas del conductor
        programaciones_activas = Programacion.objects.filter(
            driver=driver,
            container__estado__in=['asignado', 'en_ruta', 'programado']
        ).select_related('container', 'cd').order_by('fecha_programada')
        
        # Calcular ventanas de tiempo ocupadas
        ventanas_ocupadas = []
        for prog in programaciones_activas:
            ventana = cls._calcular_ventana_tiempo(prog)
            ventanas_ocupadas.append({
                'programacion_id': prog.id,
                'container_id': prog.container.container_id,
                'inicio': ventana['inicio'],
                'fin': ventana['fin'],
                'duracion_minutos': ventana['duracion_minutos']
            })
        
        # Verificar si la nueva programación se solapa con alguna existente
        nueva_inicio = programacion_nueva.fecha_programada
        nueva_fin = nueva_inicio + timedelta(minutes=tiempo_requerido + buffer_minutos)
        
        conflictos = []
        for ventana in ventanas_ocupadas:
            # Verificar solapamiento
            if cls._hay_solapamiento(nueva_inicio, nueva_fin, ventana['inicio'], ventana['fin']):
                conflictos.append(
                    f"Conflicto con {ventana['container_id']}: "
                    f"{ventana['inicio'].strftime('%H:%M')}-{ventana['fin'].strftime('%H:%M')}"
                )
        
        return {
            'disponible': len(conflictos) == 0,
            'conflictos': conflictos,
            'tiempo_requerido': tiempo_requerido,
            'ventana_ocupada': ventanas_ocupadas if ventanas_ocupadas else None,
            'nueva_ventana': {
                'inicio': nueva_inicio,
                'fin': nueva_fin
            }
        }
    
    @classmethod
    def _calcular_tiempo_total_asignacion(cls, programacion):
        """
        Calcula el tiempo total requerido para completar una asignación
        
        Incluye:
        - Tiempo de viaje al CD (Mapbox)
        - Tiempo de descarga en CD
        - Tiempo de retorno (si no es Drop & Hook)
        
        Returns:
            int: Tiempo total en minutos
        """
        cd = programacion.cd
        
        # Tiempo de descarga en el CD (del modelo CD o default)
        tiempo_descarga = cd.tiempo_promedio_descarga_min or 60
        
        # Calcular tiempo de viaje con Mapbox si el conductor tiene posición
        tiempo_viaje = 0
        if hasattr(programacion, 'driver') and programacion.driver:
            driver = programacion.driver
            if driver.ultima_posicion_lat and driver.ultima_posicion_lng and cd.lat and cd.lng:
                resultado = MapboxService.calcular_ruta(
                    float(driver.ultima_posicion_lng),
                    float(driver.ultima_posicion_lat),
                    float(cd.lng),
                    float(cd.lat)
                )
                if resultado.get('success'):
                    tiempo_viaje = int(resultado['duration_minutes'])
                else:
                    # Estimación genérica si falla Mapbox: 45 min
                    tiempo_viaje = 45
            else:
                # Sin coordenadas, usar estimación genérica
                tiempo_viaje = 45
        else:
            # Sin driver asignado aún, usar estimación
            tiempo_viaje = 45
        
        # Si el CD permite Drop & Hook, el conductor queda libre inmediatamente
        # Si no, debe esperar la descarga y potencialmente viajar de regreso
        if cd.permite_soltar_contenedor:
            # Drop & Hook: solo viaje + 15 min para soltar
            tiempo_total = tiempo_viaje + 15
        else:
            # Truck Discharge: viaje + descarga completa
            tiempo_total = tiempo_viaje + tiempo_descarga
            
            # Si requiere espera de carga, agregar tiempo adicional
            if cd.requiere_espera_carga:
                tiempo_total += 30  # 30 min adicionales por espera
        
        return tiempo_total
    
    @classmethod
    def _calcular_ventana_tiempo(cls, programacion):
        """
        Calcula la ventana de tiempo (inicio-fin) de una programación
        
        Returns:
            dict: {
                'inicio': datetime,
                'fin': datetime,
                'duracion_minutos': int
            }
        """
        duracion = cls._calcular_tiempo_total_asignacion(programacion)
        inicio = programacion.fecha_programada
        fin = inicio + timedelta(minutes=duracion)
        
        return {
            'inicio': inicio,
            'fin': fin,
            'duracion_minutos': duracion
        }
    
    @classmethod
    def _hay_solapamiento(cls, inicio1, fin1, inicio2, fin2):
        """
        Verifica si dos ventanas de tiempo se solapan
        
        Returns:
            bool: True si hay solapamiento
        """
        return inicio1 < fin2 and inicio2 < fin1
    
    @classmethod
    def obtener_proxima_ventana_disponible(cls, driver, duracion_minutos, fecha_minima=None):
        """
        Encuentra la próxima ventana de tiempo disponible para un conductor
        
        Args:
            driver: Conductor
            duracion_minutos: Duración requerida en minutos
            fecha_minima: Fecha mínima desde donde buscar (default: ahora)
        
        Returns:
            dict: {
                'disponible': bool,
                'fecha_sugerida': datetime o None,
                'ocupacion_actual': list de ventanas
            }
        """
        if fecha_minima is None:
            fecha_minima = timezone.now()
        
        # Obtener ventanas ocupadas
        programaciones = Programacion.objects.filter(
            driver=driver,
            container__estado__in=['asignado', 'en_ruta', 'programado'],
            fecha_programada__gte=fecha_minima
        ).order_by('fecha_programada')
        
        ventanas = [cls._calcular_ventana_tiempo(p) for p in programaciones]
        
        if not ventanas:
            # No tiene asignaciones, puede empezar ahora
            return {
                'disponible': True,
                'fecha_sugerida': fecha_minima,
                'ocupacion_actual': []
            }
        
        # Buscar huecos entre ventanas
        fecha_actual = fecha_minima
        for ventana in ventanas:
            # ¿Hay espacio antes de esta ventana?
            if fecha_actual + timedelta(minutes=duracion_minutos + 30) <= ventana['inicio']:
                return {
                    'disponible': True,
                    'fecha_sugerida': fecha_actual,
                    'ocupacion_actual': [{'inicio': v['inicio'], 'fin': v['fin']} for v in ventanas]
                }
            # Avanzar al final de esta ventana
            fecha_actual = ventana['fin'] + timedelta(minutes=30)  # 30 min buffer
        
        # Sugerir después de la última ventana
        return {
            'disponible': True,
            'fecha_sugerida': fecha_actual,
            'ocupacion_actual': [{'inicio': v['inicio'], 'fin': v['fin']} for v in ventanas]
        }
