"""
API para gestión de inicio de rutas con tráfico en tiempo real.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime
import logging

from apps.drivers.models import Assignment, Driver, TrafficAlert
from apps.routing.route_start_service import route_start_service
from apps.routing.driver_availability_service import driver_availability
from apps.routing.locations_catalog import get_location, list_all_locations, format_route_name

logger = logging.getLogger(__name__)


class RouteTrackingViewSet(viewsets.ViewSet):
    """
    ViewSet para tracking de rutas y alertas de tráfico en tiempo real.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='start-route')
    def start_route(self, request):
        """
        Endpoint para reportar inicio de ruta.
        
        El conductor (o sistema) reporta que inicia una ruta desde un origen
        hacia un destino. El sistema consulta Mapbox Directions API para obtener
        información de tráfico actual y genera alertas automáticas.
        
        POST /api/v1/routing/route-tracking/start-route/
        
        Body:
        {
            "assignment_id": 123,
            "driver_id": 45,
            "origin": {
                "name": "CCTI Maipú",
                "latitude": -33.5089,
                "longitude": -70.7593
            },
            "destination": {
                "name": "CD El Peñón - San Bernardo",
                "latitude": -33.6297,
                "longitude": -70.7045
            }
        }
        
        Response:
        {
            "success": true,
            "assignment_id": 123,
            "driver_name": "Juan Pérez",
            "route": {
                "origin": "CCTI Maipú",
                "destination": "CD El Peñón",
                "distance_km": 15.2
            },
            "time": {
                "departure": "2025-10-07T15:15:00Z",
                "eta": "2025-10-07T15:45:00Z",
                "duration_no_traffic": 25,
                "duration_with_traffic": 30,
                "delay": 5
            },
            "traffic": {
                "level": "medium",
                "ratio": 1.2
            },
            "alerts": [
                {
                    "id": 1,
                    "type": "TRAFFIC",
                    "message": "⚠️ TRÁFICO MEDIO DETECTADO...",
                    "traffic_level": "medium",
                    "emoji": "🟡"
                }
            ],
            "warnings": [],
            "alternative_routes": []
        }
        """
        try:
            # Validar datos de entrada
            assignment_id = request.data.get('assignment_id')
            driver_id = request.data.get('driver_id')
            origin = request.data.get('origin', {})
            destination = request.data.get('destination', {})
            
            if not all([assignment_id, driver_id, origin, destination]):
                return Response({
                    'success': False,
                    'error': 'Faltan datos requeridos',
                    'required_fields': ['assignment_id', 'driver_id', 'origin', 'destination']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar coordenadas
            required_origin_fields = ['name', 'latitude', 'longitude']
            required_dest_fields = ['name', 'latitude', 'longitude']
            
            if not all(field in origin for field in required_origin_fields):
                return Response({
                    'success': False,
                    'error': 'Datos de origen incompletos',
                    'required_fields': required_origin_fields
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not all(field in destination for field in required_dest_fields):
                return Response({
                    'success': False,
                    'error': 'Datos de destino incompletos',
                    'required_fields': required_dest_fields
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Procesar inicio de ruta
            result = route_start_service.start_route(
                assignment_id=assignment_id,
                driver_id=driver_id,
                origin_name=origin['name'],
                destination_name=destination['name'],
                origin_lat=float(origin['latitude']),
                origin_lng=float(origin['longitude']),
                dest_lat=float(destination['latitude']),
                dest_lng=float(destination['longitude'])
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Assignment.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Asignación {assignment_id} no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Driver.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Conductor {driver_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"❌ Error en start_route: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Error interno del servidor',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='alerts/active')
    def get_active_alerts(self, request):
        """
        Obtiene alertas de tráfico activas.
        
        Query params:
            - driver_id: Filtrar por conductor
            - assignment_id: Filtrar por asignación
        
        GET /api/v1/routing/route-tracking/alerts/active/?driver_id=45
        """
        driver_id = request.query_params.get('driver_id')
        assignment_id = request.query_params.get('assignment_id')
        
        alerts = TrafficAlert.objects.filter(is_active=True)
        
        if driver_id:
            alerts = alerts.filter(driver_id=driver_id)
        
        if assignment_id:
            alerts = alerts.filter(assignment_id=assignment_id)
        
        alerts = alerts.select_related('driver', 'assignment').order_by('-created_at')[:20]
        
        data = [
            {
                'id': alert.id,
                'driver': {
                    'id': alert.driver.id,
                    'name': alert.driver.nombre,
                },
                'assignment_id': alert.assignment.id,
                'route': {
                    'origin': alert.origin_name,
                    'destination': alert.destination_name,
                },
                'traffic': {
                    'level': alert.traffic_level,
                    'emoji': alert.get_traffic_emoji(),
                },
                'alert': {
                    'type': alert.alert_type,
                    'message': alert.message,
                },
                'time': {
                    'departure': alert.departure_time.isoformat(),
                    'eta': alert.estimated_arrival.isoformat(),
                    'delay_minutes': alert.delay_minutes,
                },
                'acknowledged': alert.acknowledged,
                'created_at': alert.created_at.isoformat(),
            }
            for alert in alerts
        ]
        
        return Response({
            'success': True,
            'count': len(data),
            'alerts': data
        })
    
    @action(detail=True, methods=['post'], url_path='alerts/acknowledge')
    def acknowledge_alert(self, request, pk=None):
        """
        Marca una alerta como reconocida por el conductor.
        
        POST /api/v1/routing/route-tracking/alerts/123/acknowledge/
        """
        alert = get_object_or_404(TrafficAlert, pk=pk)
        
        from django.utils import timezone
        alert.acknowledged = True
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=['acknowledged', 'acknowledged_at'])
        
        return Response({
            'success': True,
            'message': 'Alerta reconocida',
            'alert_id': alert.id
        })
    
    @action(detail=False, methods=['get'], url_path='traffic-summary')
    def traffic_summary(self, request):
        """
        Obtiene un resumen del estado de tráfico de todas las rutas activas.
        
        GET /api/v1/routing/route-tracking/traffic-summary/
        """
        from django.db.models import Count, Avg
        
        # Alertas activas por nivel de tráfico
        traffic_by_level = TrafficAlert.objects.filter(
            is_active=True
        ).values('traffic_level').annotate(
            count=Count('id')
        )
        
        # Retraso promedio
        avg_delay = TrafficAlert.objects.filter(
            is_active=True
        ).aggregate(
            avg_delay=Avg('delay_minutes')
        )
        
        # Alertas por tipo
        alerts_by_type = TrafficAlert.objects.filter(
            is_active=True
        ).values('alert_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'success': True,
            'summary': {
                'traffic_levels': list(traffic_by_level),
                'average_delay_minutes': round(avg_delay['avg_delay'] or 0, 1),
                'alerts_by_type': list(alerts_by_type),
            }
        })
    
    @action(detail=False, methods=['get'], url_path='driver-status')
    def driver_status(self, request):
        """
        Obtiene el estado actual de un conductor.
        
        GET /api/v1/routing/route-tracking/driver-status/?driver_id=45
        
        Optional:
        - check_time: ISO datetime para verificar disponibilidad futura
        
        Response:
        {
            "success": true,
            "driver_id": 45,
            "driver_name": "Juan Pérez",
            "is_available": false,
            "status": "on_route",
            "estimated_location": "En ruta (llegará en 25 min)",
            "available_at": "2025-10-07T16:00:00Z",
            "estimated_arrival": "2025-10-07T16:00:00Z",
            "current_assignment": {
                "id": 123,
                "origin": "CCTI",
                "destination": "CD El Peñón"
            }
        }
        """
        driver_id = request.query_params.get('driver_id')
        check_time_str = request.query_params.get('check_time')
        
        if not driver_id:
            return Response({
                'success': False,
                'error': 'Se requiere driver_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            driver = Driver.objects.get(id=driver_id)
            
            # Parsear check_time si existe
            check_time = None
            if check_time_str:
                try:
                    check_time = datetime.fromisoformat(check_time_str.replace('Z', '+00:00'))
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Formato de check_time inválido. Use ISO 8601'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener estado
            status_info = driver_availability.get_driver_status(driver.id, check_time)
            
            # Serializar assignment si existe
            assignment_data = None
            if status_info['current_assignment']:
                assignment = status_info['current_assignment']
                assignment_data = {
                    'id': assignment.id,
                    'container_number': assignment.container.container_number if assignment.container else None
                }
            
            return Response({
                'success': True,
                'driver_id': driver.id,
                'driver_name': driver.nombre,
                'is_available': status_info['is_available'],
                'status': status_info['status'],
                'estimated_location': status_info['estimated_location'],
                'available_at': status_info['available_at'].isoformat() if status_info['available_at'] else None,
                'estimated_arrival': status_info['estimated_arrival'].isoformat() if status_info['estimated_arrival'] else None,
                'current_assignment': assignment_data,
                'message': status_info['message']
            })
            
        except Driver.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Conductor {driver_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de conductor: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='available-drivers')
    def available_drivers(self, request):
        """
        Lista conductores disponibles en un momento específico.
        
        GET /api/v1/routing/route-tracking/available-drivers/
        
        Optional:
        - at_time: ISO datetime para verificar disponibilidad futura
        - for_location: Código de ubicación (ej: 'CCTI', 'CD_PENON')
        
        Response:
        {
            "success": true,
            "at_time": "2025-10-07T15:00:00Z",
            "count": 12,
            "drivers": [
                {
                    "driver_id": 45,
                    "nombre": "Juan Pérez",
                    "rut": "12345678-9",
                    "status": {...},
                    "priority": 1
                }
            ]
        }
        """
        at_time_str = request.query_params.get('at_time')
        for_location = request.query_params.get('for_location')
        
        # Parsear at_time si existe
        at_time = None
        if at_time_str:
            try:
                at_time = datetime.fromisoformat(at_time_str.replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Formato de at_time inválido. Use ISO 8601'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            available = driver_availability.get_available_drivers(at_time, for_location)
            
            return Response({
                'success': True,
                'at_time': (at_time or timezone.now()).isoformat(),
                'for_location': for_location,
                'count': len(available),
                'drivers': available
            })
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo conductores disponibles: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='driver-schedule')
    def driver_schedule(self, request):
        """
        Obtiene el horario de un conductor para un día específico.
        
        GET /api/v1/routing/route-tracking/driver-schedule/?driver_id=45&date=2025-10-07
        
        Response:
        {
            "success": true,
            "driver_id": 45,
            "driver_name": "Juan Pérez",
            "date": "2025-10-07",
            "schedule": [
                {
                    "assignment_id": 123,
                    "start_time": "2025-10-07T08:00:00Z",
                    "estimated_arrival": "2025-10-07T08:45:00Z",
                    "actual_arrival": null,
                    "duration_minutes": 45,
                    "status": "in_progress"
                }
            ]
        }
        """
        driver_id = request.query_params.get('driver_id')
        date_str = request.query_params.get('date')
        
        if not driver_id:
            return Response({
                'success': False,
                'error': 'Se requiere driver_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            driver = Driver.objects.get(id=driver_id)
            
            # Parsear fecha
            check_date = None
            if date_str:
                try:
                    check_date = datetime.fromisoformat(date_str)
                except ValueError:
                    return Response({
                        'success': False,
                        'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            schedule = driver_availability.get_driver_schedule(driver.id, check_date)
            
            # Serializar schedule
            schedule_data = []
            for item in schedule:
                schedule_data.append({
                    'assignment_id': item['assignment_id'],
                    'start_time': item['start_time'].isoformat() if item['start_time'] else None,
                    'estimated_arrival': item['estimated_arrival'].isoformat() if item['estimated_arrival'] else None,
                    'actual_arrival': item['actual_arrival'].isoformat() if item['actual_arrival'] else None,
                    'duration_minutes': item['duration_minutes'],
                    'status': item['status']
                })
            
            return Response({
                'success': True,
                'driver_id': driver.id,
                'driver_name': driver.nombre,
                'date': (check_date or timezone.now()).date().isoformat(),
                'schedule': schedule_data
            })
            
        except Driver.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Conductor {driver_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"❌ Error obteniendo horario: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='locations')
    def locations(self, request):
        """
        Lista todas las ubicaciones disponibles en el catálogo.
        
        GET /api/v1/routing/route-tracking/locations/
        
        Response:
        {
            "success": true,
            "count": 6,
            "locations": [
                {
                    "code": "CD_PENON",
                    "name": "CD El Peñón",
                    "full_name": "Centro de Distribución El Peñón",
                    "address": "Avenida Presidente Jorge Alessandri 18899, San Bernardo",
                    "city": "San Bernardo",
                    "region": "Región Metropolitana"
                }
            ]
        }
        """
        locations = list_all_locations()
        
        locations_data = []
        for code, loc in locations.items():
            locations_data.append({
                'code': code,
                'name': loc.name,
                'full_name': loc.full_name,
                'address': loc.address,
                'city': loc.city,
                'region': loc.region,
                'latitude': loc.latitude,
                'longitude': loc.longitude
            })
        
        return Response({
            'success': True,
            'count': len(locations_data),
            'locations': locations_data
        })
