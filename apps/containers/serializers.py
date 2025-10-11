from rest_framework import serializers
from .models import Container


class ContainerSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Container
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ContainerListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Container
        fields = [
            'id', 'container_id', 'tipo', 'estado', 'estado_display',
            'posicion_fisica', 'comuna', 'secuenciado', 'fecha_programacion'
        ]


class ContainerStockExportSerializer(serializers.ModelSerializer):
    """Serializer para exportación de stock"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Container
        fields = [
            'container_id', 'tipo', 'tipo_display', 'nave', 'vendor',
            'posicion_fisica', 'comuna', 'secuenciado', 'fecha_liberacion'
        ]
