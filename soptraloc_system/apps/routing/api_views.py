"""
API para gestión de inicio de rutas con tráfico en tiempo real.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging

from apps.drivers.models import Assignment, Driver, TrafficAlert
from apps.routing.route_start_service import route_start_service

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
        hacia un destino. El sistema consulta Google Maps API para obtener
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
