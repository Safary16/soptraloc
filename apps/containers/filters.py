"""
Filters for Container ViewSet
"""
import django_filters
from .models import Container


class ContainerFilter(django_filters.FilterSet):
    """
    Custom filter for Container model
    Supports __in lookups for estado field
    """
    estado = django_filters.CharFilter(field_name='estado', lookup_expr='exact')
    estado__in = django_filters.BaseInFilter(field_name='estado', lookup_expr='in')
    
    class Meta:
        model = Container
        fields = {
            'estado': ['exact', 'in'],
            'tipo': ['exact'],
            'secuenciado': ['exact'],
            'puerto': ['exact', 'icontains'],
            'posicion_fisica': ['exact', 'icontains'],
        }
