"""
Servicio para gestionar inicio de rutas y cálculo de tiempos en tiempo real.
Integra Google Maps API para obtener datos de tráfico actualizados.
"""
from datetime import datetime
from typing import Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction
import logging

from apps.drivers.models import Assignment, Driver, TrafficAlert
from apps.routing.google_maps_service import gmaps_service

logger = logging.getLogger(__name__)


class RouteStartService:
    """
    Servicio para procesar el inicio de una ruta.
    
    Cuando un conductor reporta que inicia una ruta:
    1. Consulta Google Maps API para obtener tiempo real con tráfico
    2. Calcula ETA considerando condiciones actuales
    3. Genera alertas si hay tráfico, accidentes o cierres
    4. Sugiere rutas alternativas si aplica
    5. Actualiza la asignación con los tiempos calculados
    """
    
    @staticmethod
    def start_route(
        assignment_id: int,
        driver_id: int,
        origin_name: str,
        destination_name: str,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> Dict:
        """
        Procesa el inicio de una ruta.
        
        Args:
            assignment_id: ID de la asignación
            driver_id: ID del conductor
            origin_name: Nombre del origen (ej: "CCTI Maipú")
            destination_name: Nombre del destino (ej: "CD El Peñón")
            origin_lat: Latitud del origen
            origin_lng: Longitud del origen
            dest_lat: Latitud del destino
            dest_lng: Longitud del destino
        
        Returns:
            Dict con información de la ruta y alertas
        """
        try:
            with transaction.atomic():
                # 1. Obtener asignación y conductor
                assignment = Assignment.objects.select_for_update().get(id=assignment_id)
                driver = Driver.objects.get(id=driver_id)
                
                # 2. Validar que el conductor corresponde a la asignación
                if assignment.conductor_id != driver_id:
                    raise ValueError(f"El conductor {driver_id} no corresponde a la asignación {assignment_id}")
                
                # 3. Obtener información de tráfico en tiempo real
                departure_time = timezone.now()
                eta, traffic_data = gmaps_service.get_eta(
                    origin_lat=origin_lat,
                    origin_lng=origin_lng,
                    dest_lat=dest_lat,
                    dest_lng=dest_lng,
                    departure_time=departure_time
                )
                
                logger.info(f"🚦 Información de tráfico obtenida para {driver.nombre}")
                logger.info(f"   Origen: {origin_name}")
                logger.info(f"   Destino: {destination_name}")
                logger.info(f"   Distancia: {traffic_data['distance_km']} km")
                logger.info(f"   Tiempo sin tráfico: {traffic_data['duration_minutes']} min")
                logger.info(f"   Tiempo con tráfico: {traffic_data['duration_in_traffic_minutes']} min")
                logger.info(f"   Nivel de tráfico: {traffic_data['traffic_level']}")
                logger.info(f"   ETA: {eta.strftime('%H:%M:%S')}")
                
                # 4. Actualizar la asignación
                assignment.tiempo_inicio_ruta = departure_time
                assignment.tiempo_llegada_estimado = eta
                assignment.ruta_minutos_estimado = traffic_data['duration_in_traffic_minutes']
                assignment.save(update_fields=[
                    'tiempo_inicio_ruta', 
                    'tiempo_llegada_estimado', 
                    'ruta_minutos_estimado'
                ])
                
                # 5. Generar alertas según condiciones de tráfico
                alerts_created = RouteStartService._generate_traffic_alerts(
                    assignment=assignment,
                    driver=driver,
                    origin_name=origin_name,
                    destination_name=destination_name,
                    departure_time=departure_time,
                    eta=eta,
                    traffic_data=traffic_data
                )
                
                # 6. Preparar respuesta
                response = {
                    'success': True,
                    'assignment_id': assignment.id,
                    'driver_name': driver.nombre,
                    'route': {
                        'origin': origin_name,
                        'destination': destination_name,
                        'distance_km': traffic_data['distance_km'],
                    },
                    'time': {
                        'departure': departure_time.isoformat(),
                        'eta': eta.isoformat(),
                        'duration_no_traffic': traffic_data['duration_minutes'],
                        'duration_with_traffic': traffic_data['duration_in_traffic_minutes'],
                        'delay': traffic_data['delay_minutes'],
                    },
                    'traffic': {
                        'level': traffic_data['traffic_level'],
                        'ratio': traffic_data['traffic_ratio'],
                    },
                    'alerts': [
                        {
                            'id': alert.id,
                            'type': alert.alert_type,
                            'message': alert.message,
                            'traffic_level': alert.traffic_level,
                            'emoji': alert.get_traffic_emoji(),
                        }
                        for alert in alerts_created
                    ],
                    'warnings': traffic_data.get('warnings', []),
                    'alternative_routes': traffic_data.get('alternative_routes', []),
                }
                
                logger.info(f"✅ Ruta iniciada exitosamente para {driver.nombre}")
                
                return response
                
        except Assignment.DoesNotExist:
            logger.error(f"❌ Asignación {assignment_id} no encontrada")
            raise
        except Driver.DoesNotExist:
            logger.error(f"❌ Conductor {driver_id} no encontrado")
            raise
        except Exception as e:
            logger.error(f"❌ Error iniciando ruta: {e}")
            raise
    
    @staticmethod
    def _generate_traffic_alerts(
        assignment: Assignment,
        driver: Driver,
        origin_name: str,
        destination_name: str,
        departure_time: datetime,
        eta: datetime,
        traffic_data: Dict
    ) -> list:
        """
        Genera alertas de tráfico según las condiciones detectadas.
        """
        alerts = []
        
        # Alerta de tráfico denso
        if traffic_data['traffic_level'] in ['high', 'very_high']:
            message = (
                f"⚠️ TRÁFICO {traffic_data['traffic_level'].upper()} DETECTADO\n\n"
                f"Ruta: {origin_name} → {destination_name}\n"
                f"Retraso estimado: +{traffic_data['delay_minutes']} minutos\n"
                f"Tiempo total: {traffic_data['duration_in_traffic_minutes']} minutos\n"
                f"ETA: {eta.strftime('%H:%M')}\n\n"
            )
            
            # Agregar advertencias si las hay
            if traffic_data.get('warnings'):
                message += "⚠️ ADVERTENCIAS:\n"
                for warning in traffic_data['warnings']:
                    message += f"• {warning}\n"
            
            alert = TrafficAlert.objects.create(
                assignment=assignment,
                driver=driver,
                origin_name=origin_name,
                destination_name=destination_name,
                traffic_level=traffic_data['traffic_level'],
                alert_type='TRAFFIC',
                estimated_time_minutes=traffic_data['duration_minutes'],
                actual_time_minutes=traffic_data['duration_in_traffic_minutes'],
                delay_minutes=traffic_data['delay_minutes'],
                departure_time=departure_time,
                estimated_arrival=eta,
                message=message,
                warnings=traffic_data.get('warnings', []),
                has_alternatives=len(traffic_data.get('alternative_routes', [])) > 0,
                alternative_routes=traffic_data.get('alternative_routes', []),
                raw_data=traffic_data,
            )
            alerts.append(alert)
            logger.info(f"🚨 Alerta de tráfico {traffic_data['traffic_level']} creada")
        
        # Alerta de rutas alternativas disponibles
        if traffic_data.get('alternative_routes') and traffic_data['delay_minutes'] > 10:
            alt_routes = traffic_data['alternative_routes']
            best_alt = min(alt_routes, key=lambda x: x['duration_minutes'])
            
            time_saved = traffic_data['duration_in_traffic_minutes'] - best_alt['duration_minutes']
            
            if time_saved > 5:  # Solo si ahorra más de 5 minutos
                message = (
                    f"💡 RUTA ALTERNATIVA RECOMENDADA\n\n"
                    f"Ruta actual: {traffic_data['duration_in_traffic_minutes']} minutos\n"
                    f"Ruta alternativa: {best_alt['duration_minutes']} minutos\n"
                    f"Ahorro: {time_saved} minutos\n\n"
                    f"Descripción: {best_alt['summary']}\n"
                )
                
                alert = TrafficAlert.objects.create(
                    assignment=assignment,
                    driver=driver,
                    origin_name=origin_name,
                    destination_name=destination_name,
                    traffic_level=traffic_data['traffic_level'],
                    alert_type='ALTERNATIVE',
                    estimated_time_minutes=traffic_data['duration_minutes'],
                    actual_time_minutes=best_alt['duration_minutes'],
                    delay_minutes=0,
                    departure_time=departure_time,
                    estimated_arrival=eta,
                    message=message,
                    warnings=[],
                    has_alternatives=True,
                    alternative_routes=alt_routes,
                    raw_data=traffic_data,
                )
                alerts.append(alert)
                logger.info(f"💡 Alerta de ruta alternativa creada (ahorro: {time_saved} min)")
        
        # Detectar accidentes/cierres en las advertencias
        if traffic_data.get('warnings'):
            for warning in traffic_data['warnings']:
                warning_lower = warning.lower()
                
                alert_type = None
                if any(word in warning_lower for word in ['accidente', 'accident', 'crash']):
                    alert_type = 'ACCIDENT'
                elif any(word in warning_lower for word in ['cerrado', 'cerrada', 'closed', 'closure']):
                    alert_type = 'ROAD_CLOSURE'
                elif any(word in warning_lower for word in ['obras', 'construction', 'roadwork']):
                    alert_type = 'CONSTRUCTION'
                
                if alert_type:
                    message = f"⚠️ {warning}"
                    
                    alert = TrafficAlert.objects.create(
                        assignment=assignment,
                        driver=driver,
                        origin_name=origin_name,
                        destination_name=destination_name,
                        traffic_level=traffic_data['traffic_level'],
                        alert_type=alert_type,
                        estimated_time_minutes=traffic_data['duration_minutes'],
                        actual_time_minutes=traffic_data['duration_in_traffic_minutes'],
                        delay_minutes=traffic_data['delay_minutes'],
                        departure_time=departure_time,
                        estimated_arrival=eta,
                        message=message,
                        warnings=[warning],
                        has_alternatives=False,
                        alternative_routes=[],
                        raw_data=traffic_data,
                    )
                    alerts.append(alert)
                    logger.info(f"⚠️  Alerta de {alert_type} creada")
        
        return alerts


# Instancia global del servicio
route_start_service = RouteStartService()
