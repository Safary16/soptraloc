from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.containers.models import Container
from apps.containers.serializers import ContainerListSerializer
from apps.programaciones.models import Programacion

from .models import SituacionCliente, SolicitudHorario
from .permissions import IsClientUser
from .serializers import SituacionClienteSerializer, SolicitudHorarioSerializer
from .services import ClientSlotRecommendationService


def _profile(user):
    return user.perfil_cliente


@require_http_methods(['GET', 'POST'])
def cliente_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'perfil_cliente'):
        return redirect('cliente_dashboard')
    if request.method == 'POST':
        user = authenticate(
            request, username=request.POST.get('username', '').strip(),
            password=request.POST.get('password', ''),
        )
        if user and hasattr(user, 'perfil_cliente') and user.perfil_cliente.empresa.activo:
            login(request, user)
            return redirect('cliente_dashboard')
        messages.error(request, 'Credenciales inválidas o usuario cliente inactivo.')
    return render(request, 'clientes/login.html')


@login_required(login_url='/cliente/login/')
def cliente_logout(request):
    logout(request)
    return redirect('cliente_login')


@login_required(login_url='/cliente/login/')
def cliente_dashboard(request):
    if not hasattr(request.user, 'perfil_cliente'):
        return redirect('cliente_login')
    return render(request, 'clientes/dashboard.html', {'empresa': _profile(request.user).empresa})


@login_required
@require_http_methods(['GET'])
def solicitudes_operaciones(request):
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'clientes/operaciones_solicitudes.html')


@api_view(['GET'])
@permission_classes([IsClientUser])
def api_stock(request):
    empresa = _profile(request.user).empresa
    queryset = Container.objects.filter(cliente_empresa=empresa).select_related('cd_entrega').order_by('-created_at')
    estado = request.query_params.get('estado')
    if estado:
        queryset = queryset.filter(estado=estado)
    return Response({
        'empresa': empresa.nombre,
        'total': queryset.count(),
        'results': ContainerListSerializer(queryset, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsClientUser])
def api_centros(request):
    empresa = _profile(request.user).empresa
    rows = empresa.centros_distribucion.filter(activo=True, tipo='cliente').values(
        'id', 'nombre', 'direccion', 'comuna', 'tiempo_promedio_descarga_min'
    )
    return Response({'results': list(rows)})


@api_view(['GET'])
@permission_classes([IsClientUser])
def api_recomendaciones(request):
    empresa = _profile(request.user).empresa
    try:
        cd = empresa.centros_distribucion.get(pk=request.query_params.get('cd'), activo=True, tipo='cliente')
        target_date = timezone.datetime.strptime(request.query_params.get('fecha', ''), '%Y-%m-%d').date()
    except (empresa.centros_distribucion.model.DoesNotExist, TypeError, ValueError):
        return Response({'error': 'CD o fecha inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(ClientSlotRecommendationService.recommend(empresa, cd, target_date))


@api_view(['GET', 'POST'])
@permission_classes([IsClientUser])
def api_solicitudes(request):
    profile = _profile(request.user)
    empresa = profile.empresa
    if request.method == 'GET':
        rows = SolicitudHorario.objects.filter(empresa=empresa).select_related('container', 'cd', 'solicitante')
        return Response({'results': SolicitudHorarioSerializer(rows, many=True).data})
    if not profile.puede_solicitar:
        return Response({'error': 'Este usuario no puede crear solicitudes.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        container = Container.objects.get(pk=request.data.get('container'), cliente_empresa=empresa)
        cd = empresa.centros_distribucion.get(pk=request.data.get('cd'), activo=True, tipo='cliente')
        inicio = timezone.datetime.fromisoformat(str(request.data.get('inicio')).replace('Z', '+00:00'))
        fin = timezone.datetime.fromisoformat(str(request.data.get('fin')).replace('Z', '+00:00'))
        if timezone.is_naive(inicio):
            inicio = timezone.make_aware(inicio)
        if timezone.is_naive(fin):
            fin = timezone.make_aware(fin)
    except (Container.DoesNotExist, empresa.centros_distribucion.model.DoesNotExist, TypeError, ValueError):
        return Response({'error': 'Contenedor, CD o horario inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    if container.estado not in {'liberado', 'secuenciado'}:
        return Response({'error': 'Solo se puede solicitar horario para contenedores liberados.'}, status=status.HTTP_400_BAD_REQUEST)
    if inicio <= timezone.now() or fin <= inicio or fin - inicio > timedelta(hours=8):
        return Response({'error': 'La ventana debe ser futura, válida y no superar 8 horas.'}, status=status.HTTP_400_BAD_REQUEST)
    modo = request.data.get('modo')
    if modo not in {'recomendado', 'manual'}:
        return Response({'error': 'Modo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    snapshot = request.data.get('recomendacion_snapshot') if modo == 'recomendado' else {}
    try:
        solicitud = SolicitudHorario.objects.create(
            empresa=empresa, solicitante=request.user, container=container, cd=cd,
            modo=modo, inicio_solicitado=inicio, fin_solicitado=fin,
            recomendacion_snapshot=snapshot if isinstance(snapshot, dict) else {},
            observaciones_cliente=str(request.data.get('observaciones', ''))[:2000],
        )
    except IntegrityError:
        return Response({'error': 'Ya existe una solicitud pendiente para este contenedor.'}, status=status.HTTP_409_CONFLICT)
    return Response(SolicitudHorarioSerializer(solicitud).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsClientUser])
def api_situaciones(request):
    profile = _profile(request.user)
    empresa = profile.empresa
    if request.method == 'GET':
        rows = SituacionCliente.objects.filter(empresa=empresa).select_related('container', 'creada_por')
        return Response({'results': SituacionClienteSerializer(rows, many=True).data})
    container = None
    container_id = request.data.get('container')
    if container_id:
        try:
            container = Container.objects.get(pk=container_id, cliente_empresa=empresa)
        except (Container.DoesNotExist, TypeError, ValueError):
            return Response({'error': 'El contenedor no pertenece a la empresa.'}, status=status.HTTP_400_BAD_REQUEST)
    categoria = request.data.get('categoria', 'operativa')
    prioridad = request.data.get('prioridad', 'normal')
    if categoria not in dict(SituacionCliente.CATEGORIAS):
        return Response({'error': 'Categoría inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    if prioridad not in dict(SituacionCliente.PRIORIDADES):
        return Response({'error': 'Prioridad inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    asunto = str(request.data.get('asunto', '')).strip()[:160]
    mensaje = str(request.data.get('mensaje', '')).strip()[:4000]
    if not asunto or not mensaje:
        return Response({'error': 'Asunto y mensaje son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)
    row = SituacionCliente.objects.create(
        empresa=empresa, creada_por=request.user, container=container,
        categoria=categoria, prioridad=prioridad, asunto=asunto, mensaje=mensaje,
    )
    return Response(SituacionClienteSerializer(row).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_situaciones_operaciones(request):
    rows = SituacionCliente.objects.select_related('empresa', 'container', 'creada_por').all()
    estado = request.query_params.get('estado')
    if estado:
        rows = rows.filter(estado=estado)
    return Response({'results': SituacionClienteSerializer(rows, many=True).data})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_revisar_situacion(request, pk):
    try:
        row = SituacionCliente.objects.get(pk=pk)
    except SituacionCliente.DoesNotExist:
        return Response({'error': 'Situación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    nuevo_estado = request.data.get('estado')
    if nuevo_estado not in dict(SituacionCliente.ESTADOS):
        return Response({'error': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    row.estado = nuevo_estado
    row.respuesta_operaciones = str(request.data.get('respuesta', '')).strip()[:4000]
    row.revisada_por = request.user
    row.revisada_at = timezone.now()
    row.save(update_fields=['estado', 'respuesta_operaciones', 'revisada_por', 'revisada_at', 'updated_at'])
    return Response(SituacionClienteSerializer(row).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_solicitudes_operaciones(request):
    rows = SolicitudHorario.objects.select_related('empresa', 'container', 'cd', 'solicitante').all()
    estado = request.query_params.get('estado')
    if estado:
        rows = rows.filter(estado=estado)
    return Response({'results': SolicitudHorarioSerializer(rows, many=True).data})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_revisar_solicitud(request, pk):
    decision = request.data.get('decision')
    if decision not in {'aceptada', 'ajustada', 'rechazada'}:
        return Response({'error': 'Decisión inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        try:
            solicitud = SolicitudHorario.objects.select_for_update().select_related('container', 'cd').get(pk=pk)
        except SolicitudHorario.DoesNotExist:
            return Response({'error': 'Solicitud no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        if solicitud.estado != 'pendiente':
            return Response({'error': 'La solicitud ya fue revisada.'}, status=status.HTTP_409_CONFLICT)
        solicitud.estado = decision
        solicitud.respuesta_operaciones = str(request.data.get('respuesta', ''))[:2000]
        solicitud.revisado_por = request.user
        solicitud.revisado_at = timezone.now()
        if decision != 'rechazada':
            try:
                inicio = timezone.datetime.fromisoformat(str(request.data.get('inicio') or solicitud.inicio_solicitado.isoformat()).replace('Z', '+00:00'))
                fin = timezone.datetime.fromisoformat(str(request.data.get('fin') or solicitud.fin_solicitado.isoformat()).replace('Z', '+00:00'))
                if timezone.is_naive(inicio): inicio = timezone.make_aware(inicio)
                if timezone.is_naive(fin): fin = timezone.make_aware(fin)
            except (TypeError, ValueError):
                return Response({'error': 'Horario confirmado inválido.'}, status=status.HTTP_400_BAD_REQUEST)
            if fin <= inicio:
                return Response({'error': 'La ventana confirmada es inválida.'}, status=status.HTTP_400_BAD_REQUEST)
            container = solicitud.container
            if container.estado not in {'liberado', 'secuenciado', 'programado'}:
                return Response({'error': 'El contenedor ya no está disponible para programación.'}, status=status.HTTP_409_CONFLICT)
            programacion, _ = Programacion.objects.update_or_create(
                container=container,
                defaults={
                    'cd': solicitud.cd, 'fecha_programada': inicio,
                    'cliente': solicitud.empresa.nombre,
                    'direccion_entrega': solicitud.cd.direccion,
                    'observaciones': solicitud.observaciones_cliente,
                    'ventana_horaria_inicio': inicio, 'ventana_horaria_fin': fin,
                    'decision_operador': 'CONFIRMAR' if decision == 'aceptada' else 'MODIFICAR',
                },
            )
            if container.estado in {'liberado', 'secuenciado'}:
                container.cd_entrega = solicitud.cd
                container.fecha_programacion = inicio
                container.save(update_fields=['cd_entrega', 'fecha_programacion', 'updated_at'])
                container.cambiar_estado('programado', request.user.username)
            solicitud.inicio_confirmado = inicio
            solicitud.fin_confirmado = fin
            solicitud.programacion = programacion
        solicitud.save()
    return Response(SolicitudHorarioSerializer(solicitud).data)
