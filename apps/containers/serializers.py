from rest_framework import serializers
from .models import Container


class ContainerSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    container_id_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = Container
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ContainerListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_movimiento_display = serializers.CharField(source='get_tipo_movimiento_display', read_only=True)
    tipo_carga_display = serializers.CharField(source='get_tipo_carga_display', read_only=True)
    cd_entrega_nombre = serializers.CharField(source='cd_entrega.nombre', read_only=True)
    container_id_formatted = serializers.ReadOnlyField()
    peso_total = serializers.ReadOnlyField()
    dias_para_demurrage = serializers.ReadOnlyField()
    urgencia_demurrage = serializers.ReadOnlyField()
    
    class Meta:
        model = Container
        fields = [
            'id', 'container_id', 'container_id_formatted', 'tipo', 'tipo_carga', 'tipo_carga_display',
            'estado', 'estado_display', 'nave',
            'peso_carga', 'tara', 'peso_total', 'contenido',
            'posicion_fisica', 'comuna', 'secuenciado', 'fecha_programacion',
            'fecha_eta', 'fecha_demurrage', 'dias_para_demurrage', 'urgencia_demurrage',
            'deposito_devolucion', 'tipo_movimiento', 'tipo_movimiento_display',
            'cd_entrega', 'cd_entrega_nombre', 'fecha_descarga'
        ]


class ContainerStockExportSerializer(serializers.ModelSerializer):
    """Serializer para exportación de stock"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    dias_hasta_demurrage = serializers.SerializerMethodField()
    
    class Meta:
        model = Container
        fields = [
            'container_id', 'tipo', 'tipo_display', 'nave', 'vendor',
            'posicion_fisica', 'comuna', 'secuenciado', 'fecha_liberacion',
            'fecha_eta', 'fecha_demurrage', 'dias_hasta_demurrage', 'deposito_devolucion'
        ]
    
    def get_dias_hasta_demurrage(self, obj):
        """Calcula días hasta demurrage, negativo si ya venció"""
        if not obj.fecha_demurrage:
            return None
        from django.utils import timezone
        delta = obj.fecha_demurrage - timezone.now()
        return delta.days
