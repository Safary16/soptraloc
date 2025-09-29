from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from apps.containers.models import Container
from apps.containers.services.status_utils import (
    ACTIVE_STATUS_CODES,
    active_status_filter_values,
    normalize_status,
    related_status_values,
    summarize_statuses,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    """
    Endpoint para obtener token JWT para testing
    
    POST /api/v1/auth/token/
    {
        "username": "admin",
        "password": "admin123"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Se requieren username y password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
            },
            'usage': {
                'header': f'Authorization: Bearer {str(refresh.access_token)}',
                'example_curl': f'curl -H "Authorization: Bearer {str(refresh.access_token)}" http://localhost:8000/api/v1/containers/'
            }
        })
    else:
        return Response({
            'error': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def auth_info(request):
    """
    Información sobre autenticación del sistema
    """
    return Response({
        'message': 'Sistema SoptraLoc - Autenticación JWT',
        'endpoints': {
            'obtain_token': '/api/v1/auth/token/',
            'containers': '/api/v1/containers/',
            'admin': '/admin/',
            'dashboard': '/dashboard/',
        },
        'default_credentials': {
            'username': 'admin',
            'password': 'admin123',
            'note': 'Usar endpoint /api/v1/auth/token/ para obtener JWT'
        },
        'stats': {
            'total_containers': Container.objects.count(),
            'containers_programados': Container.objects.filter(status__in=related_status_values('PROGRAMADO')).count(),
        },
        'headers_required': {
            'Authorization': 'Bearer <your_jwt_token>',
        }
    })


def home_view(request):
    """Vista principal con dashboard básico"""
    programados = Container.objects.filter(status__in=related_status_values('PROGRAMADO')).count()
    total = Container.objects.count()
    
    return render(request, 'core/home.html', {
        'title': 'SoptraLoc - Sistema de Gestión Logística',
        'programados': programados,
        'total': total
    })


@login_required
def dashboard_view(request):
    """Dashboard principal con contenedores programados"""
    from datetime import timedelta
    from apps.drivers.models import Alert

    status_filter = request.GET.get('status', 'all')
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)

    base_queryset = Container.objects.select_related(
        'conductor_asignado',
        'client',
        'terminal',
        'owner_company',
        'vessel',
        'agency',
        'shipping_line'
    )

    if status_filter == 'all':
        containers = base_queryset.filter(status__in=active_status_filter_values())
    else:
        normalized_status = normalize_status(status_filter)
        containers = base_queryset.filter(status__in=related_status_values(normalized_status))

    containers = containers.order_by('scheduled_date', 'container_number')

    raw_status_counts = Container.objects.values_list('status').annotate(count=Count('id'))
    normalized_counts = {
        summary.code: summary.count for summary in summarize_statuses(raw_status_counts)
    }

    stats = {
        'total': sum(normalized_counts.values()),
        'programados': normalized_counts.get('PROGRAMADO', 0),
        'en_proceso': normalized_counts.get('EN_PROCESO', 0),
        'en_transito': normalized_counts.get('EN_TRANSITO', 0),
        'liberados': normalized_counts.get('LIBERADO', 0),
        'descargados': normalized_counts.get('DESCARGADO', 0),
        'en_secuencia': normalized_counts.get('EN_SECUENCIA', 0),
    }

    programados_hoy_data = list(
        Container.objects.filter(
            status__in=related_status_values('PROGRAMADO'),
            scheduled_date=today,
            conductor_asignado__isnull=True
        ).values('id', 'container_number')
    )
    programados_hoy_ids = [item['id'] for item in programados_hoy_data]

    if programados_hoy_ids:
        existing_alert_ids = set(
            Alert.objects.filter(
                tipo='CONTENEDOR_SIN_ASIGNAR',
                container_id__in=programados_hoy_ids,
                is_active=True
            ).values_list('container_id', flat=True)
        )
        new_alerts = [
            Alert(
                tipo='CONTENEDOR_SIN_ASIGNAR',
                prioridad='ALTA',
                titulo=f"Contenedor {item['container_number']} sin conductor",
                mensaje=(
                    f"El contenedor {item['container_number']} está programado para hoy y no tiene conductor asignado."
                ),
                container_id=item['id']
            )
            for item in programados_hoy_data
            if item['id'] not in existing_alert_ids
        ]
        if new_alerts:
            Alert.objects.bulk_create(new_alerts)

    context = {
        'title': 'Dashboard - SoptraLoc',
        'containers': containers,
        'status_filter': status_filter,
        'today': today,
        'tomorrow': tomorrow,
        'stats': stats,
        'alertas_activas': Alert.objects.filter(is_active=True).count(),
        'contenedores_sin_asignar': len(programados_hoy_data),
    }

    return render(request, 'core/dashboard.html', context)


@login_required
def resueltos_view(request):
    """Vista para contenedores resueltos (asignados)"""
    # Filtrar contenedores asignados o en proceso
    contenedores_resueltos = Container.objects.filter(
        conductor_asignado__isnull=False
    ).select_related(
        'conductor_asignado', 'client', 'terminal', 'vessel', 'agency', 'shipping_line'
    ).order_by('-scheduled_date', 'container_number')
    
    # Filtros adicionales
    estado_filter = request.GET.get('estado')
    conductor_filter = request.GET.get('conductor')
    
    if estado_filter:
        contenedores_resueltos = contenedores_resueltos.filter(status=estado_filter)
    
    if conductor_filter:
        contenedores_resueltos = contenedores_resueltos.filter(conductor_asignado_id=conductor_filter)
    
    # Estadísticas
    stats = {
        'total_resueltos': contenedores_resueltos.count(),
        'asignados': contenedores_resueltos.filter(status='ASIGNADO').count(),
        'en_ruta': contenedores_resueltos.filter(status='EN_RUTA').count(),
        'arribados': contenedores_resueltos.filter(status='ARRIBADO').count(),
        'finalizados': contenedores_resueltos.filter(status='FINALIZADO').count(),
    }
    
    # Lista de conductores para el filtro
    from apps.drivers.models import Driver
    conductores = Driver.objects.filter(is_active=True).order_by('nombre')
    
    context = {
        'title': 'Contenedores Resueltos - SoptraLoc',
        'contenedores': contenedores_resueltos,
        'stats': stats,
        'conductores': conductores,
        'estado_filter': estado_filter,
        'conductor_filter': conductor_filter,
        'today': timezone.now().date(),
    }
    
    return render(request, 'core/resueltos.html', context)