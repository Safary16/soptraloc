"""
Filters for Programacion ViewSet.

Corrige hallazgos de auditoría 2026-09-22 (N3 + N9):
- `driver__isnull=true` usado por asignacion.html (pendientes sin asignar)
- `fecha_asignacion__gte` usado por asignacion.html (asignados hoy)
- `cliente` con matching insensible a mayúsculas y normalizado
  (el frontend puede enviar "WALMART" y el valor canónico es "Walmart")
"""
import django_filters

from apps.core.utils import normalizar_cliente

from .models import Programacion


class ProgramacionFilter(django_filters.FilterSet):
    # Panel de asignación: ?driver__isnull=true → solo pendientes
    driver__isnull = django_filters.BooleanFilter(field_name='driver', lookup_expr='isnull')

    # Panel de asignación: ?fecha_asignacion__gte=... → asignados desde X
    fecha_asignacion__gte = django_filters.DateTimeFilter(
        field_name='fecha_asignacion', lookup_expr='gte'
    )

    # Cliente: insensible a mayúsculas + normalización canónica (N9)
    cliente = django_filters.CharFilter(method='filter_cliente')

    class Meta:
        model = Programacion
        fields = ['fecha_programada', 'requiere_alerta', 'driver', 'cd']

    def filter_cliente(self, queryset, name, value):
        canonico = normalizar_cliente(value)
        return queryset.filter(cliente__iexact=canonico)
