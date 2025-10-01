"""
Vistas API para routing y tiempos
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta

from .models import LocationPair, OperationTime, Route, RouteStop, ActualTripRecord
from .ml_service import TimePredictionML


class TimePredictionViewSet(viewsets.ViewSet):
    """
    API para consultar predicciones de tiempo.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='predict-route')
    def predict_route(self, request):
        """
        Predice tiempo de viaje entre dos ubicaciones.
        
        POST /api/routing/time-prediction/predict-route/
        Body: {
            "origin_id": 1,
            "destination_id": 2,
            "departure_time": "2025-10-01T14:30:00Z"  // opcional
        }
        """
        origin_id = request.data.get('origin_id')
        destination_id = request.data.get('destination_id')
        departure_time_str = request.data.get('departure_time')
        
        if not origin_id or not destination_id:
            return Response(
                {'error': 'origin_id y destination_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parsear departure_time si existe
        departure_time = None
        if departure_time_str:
            try:
                departure_time = datetime.fromisoformat(departure_time_str.replace('Z', '+00:00'))
            except ValueError:
                return Response(
                    {'error': 'Formato de departure_time inválido. Use ISO 8601'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Obtener predicción
        prediction = TimePredictionML.get_prediction_for_route(
            origin_id,
            destination_id,
            departure_time
        )
        
        if prediction.get('error'):
            return Response(prediction, status=status.HTTP_404_NOT_FOUND)
        
        return Response(prediction)
    
    @action(detail=False, methods=['get'], url_path='accuracy-report')
    def accuracy_report(self, request):
        """
        Retorna reporte de precisión del modelo ML.
        
        GET /api/routing/time-prediction/accuracy-report/
        """
        report = TimePredictionML.analyze_prediction_accuracy()
        return Response(report)
    
    @action(detail=False, methods=['get'], url_path='optimization-suggestions')
    def optimization_suggestions(self, request):
        """
        Retorna sugerencias de optimización.
        
        GET /api/routing/time-prediction/optimization-suggestions/
        """
        suggestions = TimePredictionML.suggest_route_optimizations()
        return Response({
            'total_suggestions': len(suggestions),
            'suggestions': suggestions
        })
    
    @action(detail=False, methods=['post'], url_path='update-ml')
    def update_ml(self, request):
        """
        Fuerza actualización de predicciones ML.
        
        POST /api/routing/time-prediction/update-ml/
        """
        result = TimePredictionML.update_all_predictions()
        return Response({
            'status': 'success',
            'message': 'Predicciones ML actualizadas',
            'location_pairs_updated': result['location_pairs'],
            'operations_updated': result['operations'],
            'timestamp': result['timestamp']
        })


class RouteViewSet(viewsets.ViewSet):
    """
    API para gestión de rutas.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='today')
    def today_routes(self, request):
        """
        Retorna rutas del día actual.
        
        GET /api/routing/routes/today/
        """
        today = timezone.now().date()
        routes = Route.objects.filter(
            route_date=today,
            is_active=True
        ).select_related('driver', 'vehicle')
        
        data = []
        for route in routes:
            data.append({
                'id': str(route.id),
                'name': route.name,
                'driver': {
                    'id': str(route.driver.id),
                    'name': f"{route.driver.first_name} {route.driver.last_name}"
                } if route.driver else None,
                'status': route.status,
                'total_containers': route.total_containers,
                'completed_stops': route.completed_stops,
                'progress_percent': (route.completed_stops / route.total_containers * 100) if route.total_containers > 0 else 0,
                'estimated_duration': route.estimated_duration,
                'actual_duration': route.actual_duration,
            })
        
        return Response({
            'date': today,
            'total_routes': len(data),
            'routes': data
        })
    
    @action(detail=True, methods=['post'], url_path='start')
    def start_route(self, request, pk=None):
        """
        Inicia una ruta.
        
        POST /api/routing/routes/{id}/start/
        """
        try:
            route = Route.objects.get(pk=pk)
        except Route.DoesNotExist:
            return Response(
                {'error': 'Ruta no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if route.status != 'PLANNED':
            return Response(
                {'error': f'La ruta debe estar en estado PLANNED. Estado actual: {route.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        route.status = 'IN_PROGRESS'
        route.actual_start = timezone.now()
        route.save()
        
        return Response({
            'status': 'success',
            'message': 'Ruta iniciada',
            'route_id': str(route.id),
            'actual_start': route.actual_start
        })
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_route(self, request, pk=None):
        """
        Completa una ruta.
        
        POST /api/routing/routes/{id}/complete/
        """
        try:
            route = Route.objects.get(pk=pk)
        except Route.DoesNotExist:
            return Response(
                {'error': 'Ruta no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        route.status = 'COMPLETED'
        route.actual_end = timezone.now()
        
        if route.actual_start:
            delta = route.actual_end - route.actual_start
            route.actual_duration = int(delta.total_seconds() / 60)
        
        route.save()
        
        return Response({
            'status': 'success',
            'message': 'Ruta completada',
            'route_id': str(route.id),
            'actual_duration': route.actual_duration
        })


class RouteStopViewSet(viewsets.ViewSet):
    """
    API para gestión de paradas de ruta.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_stop(self, request, pk=None):
        """
        Marca una parada como completada.
        
        POST /api/routing/route-stops/{id}/complete/
        Body: {
            "actual_departure": "2025-10-01T15:30:00Z",  // opcional
            "notes": "Entrega sin problemas"  // opcional
        }
        """
        try:
            stop = RouteStop.objects.get(pk=pk)
        except RouteStop.DoesNotExist:
            return Response(
                {'error': 'Parada no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        actual_departure = request.data.get('actual_departure')
        notes = request.data.get('notes', '')
        
        # Parsear tiempo si existe
        departure_time = None
        if actual_departure:
            try:
                departure_time = datetime.fromisoformat(actual_departure.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        stop.mark_completed(
            actual_departure_time=departure_time,
            notes=notes
        )
        
        return Response({
            'status': 'success',
            'message': 'Parada completada',
            'stop_id': str(stop.id),
            'actual_operation_time': stop.actual_operation_time,
            'delay_minutes': stop.delay_minutes
        })
