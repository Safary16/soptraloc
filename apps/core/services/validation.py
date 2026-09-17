"""
Servicio de validación de pre-asignación con cálculos de tiempo
Previene conflictos de doble asignación usando tiempos reales de Mapbox
"""
from datetime import timedelta
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
                'conflictos': [{
                    'container_id': '—',
                    'retraso_min': 0,
                    'mensaje': 'Conductor no disponible (presente=False o asignaciones completas)'
                }],
                'retraso_maximo_min': 0,
                'tiempo_requerido': 0,
                'ventana_ocupada': None,
                'nueva_ventana': None
            }
        
        # Calcular tiempo requerido para la nueva asignación
        tiempo_requerido = cls._calcular_tiempo_total_asignacion(programacion_nueva)
        
        # Obtener todas las programaciones activas del conductor
        # Incluye estados que ocupan agenda real del conductor hoy
        # (entregado/soltado/descargado recientes siguen ocupando hasta su fin llamativo
        #  para no asignar un 2° servicio antes de que el anterior se cierre del todo)
        programaciones_activas = Programacion.objects.filter(
            driver=driver,
            container__estado__in=[
                'asignado', 'en_ruta', 'programado',
                'entregado', 'soltado', 'descargado'
            ]
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
                'duracion_minutos': ventana['duracion_minutos'],
                'estado_servicio': ventana.get('estado_servicio', 'ASIGNADO')
            })
        
        # Verificar si la nueva programación se solapa con alguna existente
        nueva_inicio = programacion_nueva.fecha_programada
        nueva_fin = nueva_inicio + timedelta(minutes=tiempo_requerido + buffer_minutos)
        
        conflictos = []
        retraso_maximo_min = 0
        for ventana in ventanas_ocupadas:
            # Verificar solapamiento
            if cls._hay_solapamiento(nueva_inicio, nueva_fin, ventana['inicio'], ventana['fin']):
                # Déficit real: cuántos minutos arranca el 2° servicio después de que
                # debería terminar el 1° (según viaje + descarga estimados).
                # Si el conductor sigue ocupado hasta esa hora, el 2° servicio
                # parte tarde con ese déficit.
                retraso_min = max(0, int((ventana['fin'] - nueva_inicio).total_seconds() / 60))
                if retraso_min > retraso_maximo_min:
                    retraso_maximo_min = retraso_min
                # Estado operativo del servicio existente para un aviso más claro
                estado_serv = ventana.get('estado_servicio', 'activo')
                ctx = {
                    'EN RUTA': 'va en ruta y según ETA terminaría a las',
                    'ENTREGADO': 'fue entregado y quedó libre para las',
                    'ASIGNADO': 'está programado hasta las',
                }
                desc_estado = ctx.get(estado_serv, 'ocupa al conductor hasta las')
                conflictos.append({
                    'programacion_id': ventana['programacion_id'],
                    'container_id': ventana['container_id'],
                    'estado_servicio': estado_serv,
                    'inicio_servicio_existente': ventana['inicio'].isoformat(),
                    'fin_servicio_existente': ventana['fin'].isoformat(),
                    'retraso_min': retraso_min,
                    'mensaje': (
                        f"El conductor ya tiene {ventana['container_id']} ({estado_serv.replace('_', ' ').lower()}) "
                        f"que {desc_estado} {ventana['fin'].strftime('%H:%M')} "
                        f"(estimado ETA: {ventana['duracion_minutos']} min); este 2° servicio comenzaría a las "
                        f"{nueva_inicio.strftime('%H:%M')} → llegaría con ≈{retraso_min} min de retraso "
                        f"según estimación (viaje + descarga)."
                    ),
                })
        
        return {
            'disponible': len(conflictos) == 0,
            'conflictos': conflictos,
            'retraso_maximo_min': retraso_maximo_min,
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
        Calcula la ventana de tiempo (inicio-fin) de una programación.
        
        Real / operativo:
        - Si el contenedor YA está EN RUTA, la ventana parte del inicio real
          (fecha_inicio_ruta) y termina en inicio + ETA calculada (eta_minutos),
          NO en la fecha_programada teórica.
        - Si quedó entregado/soltado/descargado recién, la ventana termina en
          la hora real de cierre (fecha_arribo_cd/fecha_descarga) para no
          pisar al conductor con un 2° servicio inmediato.
        - Si está programado/asignado (aún sin salir), ventana teórica desde
          fecha_programada.
        """
        container = programacion.container
        estado = container.estado
        
        # 1) En ruta: usar inicio real + ETA operativa (clic de la máquina)
        if estado == 'en_ruta' and programacion.fecha_inicio_ruta:
            inicio = programacion.fecha_inicio_ruta
            if programacion.eta_minutos:
                duracion = int(programacion.eta_minutos)
            else:
                duracion = cls._calcular_tiempo_total_asignacion(programacion)
            fin = inicio + timedelta(minutes=duracion)
            return {
                'inicio': inicio,
                'fin': fin,
                'duracion_minutos': duracion,
                'estado_servicio': 'EN_RUTA',
            }
        
        # 2) Cerrado recién (entregado/soltado/descargado): usar fin real
        if estado in ('entregado', 'soltado', 'descargado'):
            fin_real = programacion.fecha_arribo_cd or programacion.fecha_inicio_ruta
            if fin_real:
                duracion = cls._calcular_tiempo_total_asignacion(programacion)
                inicio = fin_real
                # El conductor se libera al cerrar el servicio (~tiempo de descarga restante
                # = 0 para la agenda siguiente); la ventana puntual marca el cierre.
                return {
                    'inicio': inicio,
                    'fin': fin_real,
                    'duracion_minutos': 0,
                    'estado_servicio': 'ENTREGADO',
                }
        
        # 3) Programado/asignado (sin salir aún): ventana teórica
        duracion = cls._calcular_tiempo_total_asignacion(programacion)
        inicio = programacion.fecha_programada
        fin = inicio + timedelta(minutes=duracion)
        return {
            'inicio': inicio,
            'fin': fin,
            'duracion_minutos': duracion,
            'estado_servicio': 'ASIGNADO',
        }
    
    @classmethod
    def _hay_solapamiento(cls, inicio1, fin1, inicio2, fin2):
        """
        Verifica si dos ventanas de tiempo se solapan
        
        Returns:
            bool: True si hay solapamiento
        """
        return inicio1 < fin2 and inicio2 < fin1
    
