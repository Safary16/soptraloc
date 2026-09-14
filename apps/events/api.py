"""
API de auditoría: expone el registro de eventos del sistema.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.events.models import Event
from apps.events.serializers import EventSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def auditoria_events(request):
    """
    Lista eventos de auditoría con filtros opcionales:
      ?container_id=... (id numérico o container_id texto)
      ?event_type=...
      ?limit=200 (default 100)
      ?offset=0
    """
    qs = Event.objects.select_related('container').all()

    container_id = request.query_params.get('container_id', '').strip()
    if container_id:
        from apps.containers.models import Container
        norm = Container.normalize_container_id(container_id)
        qs = qs.filter(container_id=norm)

    event_type = request.query_params.get('event_type', '').strip()
    if event_type:
        qs = qs.filter(event_type=event_type)

    limit = min(int(request.query_params.get('limit', 100)), 500)
    offset = max(int(request.query_params.get('offset', 0)), 0)

    total = qs.count()
    eventos = qs.order_by('-created_at')[offset:offset + limit]

    types = [{'value': v, 'label': l} for v, l in Event.EVENT_TYPES]
    return Response({
        'success': True,
        'total': total,
        'limit': limit,
        'offset': offset,
        'event_types': types,
        'eventos': EventSerializer(eventos, many=True).data,
    })