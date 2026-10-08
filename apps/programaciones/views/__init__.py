from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db import transaction
import logging

from ..filters import ProgramacionFilter
from ..models import Programacion
from ..serializers import (
    ProgramacionSerializer,
    ProgramacionListSerializer,
    ProgramacionCreateSerializer
)


logger = logging.getLogger(__name__)

"""Package de vistas de programaciones (iteración 10: partir views.py por dominios).
ProgramacionViewSet se compone de 4 mixins por dominio; el routing DRF no cambia
(mismo nombre de clase, mismas 32 actions).
"""

class ProgramacionViewSetBase:
    """Attrs del ViewSet + métodos base (serializer routing, destroy)."""

    def get_serializer_class(self):
        if self.action == 'list':
            return ProgramacionListSerializer
        elif self.action == 'create':
            return ProgramacionCreateSerializer
        return ProgramacionSerializer


    def perform_destroy(self, instance):
        """Elimina una programación evitando IntegrityError por la relación
        OneToOne entre Container y Programacion y por filas hijas que
        referencian al contenedor asociado.

        Comportamiento:
        1. Deslinkea el contenedor (libera container.estado, limpia fechas y
           el OneToOne inverso para evitar UNIQUE collisions si el operador
           re-crea inmediatamente la programacion).
        2. Borra la programacion (cascade a RegistroOperacion, SET_NULL en
           TiempoViaje/TiempoOperacion, CASCADE en Eventos).

        Sin esto, el DELETE del frontend (operaciones.html → eliminarPreAsignacion)
        podia fallar con IntegrityError en escenarios de re-asignacion inmediata.
        """
        with transaction.atomic():
            container = getattr(instance, 'container', None)
            if container is not None:
                # Limpiar estado y timestamps del contenedor para que no quede
                # colgado en 'programado'/'asignado' tras la baja. Usamos
                # cambiar_estado que respeta el FSM; si el estado no permite
                # transicion directa, forzar via atributo y save (caso admin).
                try:
                    estado_actual = getattr(container, 'estado', None)
                    if estado_actual in ('programado', 'asignado', 'secuenciado', 'incidente'):
                        # Cancelado es el destino valido desde varios estados FSM.
                        container.cambiar_estado('cancelado')
                    elif estado_actual in ('en_patio', 'por_arribar', 'liberado'):
                        # No requiere cambio de estado; solo limpia timestamps stale.
                        pass
                    # Reset timestamps operativos sobre el contenedor.
                    update_fields = []
                    for f in (
                        'fecha_programacion', 'fecha_secuenciado', 'fecha_asignacion',
                        'fecha_incidente', 'fecha_inicio_ruta',
                    ):
                        if getattr(container, f, None) is not None:
                            setattr(container, f, None)
                            update_fields.append(f)
                    if update_fields:
                        container.save(update_fields=update_fields)
                except Exception:
                    logger.exception(
                        'No se pudo limpiar el contenedor asociado a la programacion %s; '
                        'se procede al DELETE igualmente.', instance.pk,
                    )
            instance.delete()



from .mixins_consulta import ConsultaMixin
from .mixins_asignacion import AsignacionMixin
from .mixins_flujo_conductor import FlujoConductorMixin
from .mixins_rutas_ml import RutasMlMixin


class ProgramacionViewSet(
    ProgramacionViewSetBase,
    AsignacionMixin,
    FlujoConductorMixin,
    RutasMlMixin,
    ConsultaMixin,
    viewsets.ModelViewSet,
):
    """
    ViewSet para gestión de programaciones — compuesto por mixins de dominio.
    MRO documentado: base primero (attrs), ConsultaMixin último para que los
    helpers (_usuario_puede_operar_viaje, _registrar_arribo,
    _update_registro_operacion_on_completion) resuelvan siempre.
    """
    queryset = Programacion.objects.select_related('container', 'driver', 'cd').all()
    serializer_class = ProgramacionSerializer
    # N3/N9 (auditoría 2026-09-22): filterset con lookups que el panel de
    # asignación ya enviaba (driver__isnull, fecha_asignacion__gte) y cliente
    # normalizado + iexact. Ver apps/programaciones/filters.py
    filterset_class = ProgramacionFilter
    search_fields = ['container__container_id', 'cliente']
    ordering_fields = ['fecha_programada', 'created_at']
    ordering = ['fecha_programada']
    permission_classes = [IsAuthenticatedOrReadOnly]
