from rest_framework import serializers
from .models import CD


class CDSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    puede_recibir_vacios = serializers.BooleanField(read_only=True)
    espacios_disponibles = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CD
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CDListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = CD
        fields = [
            'id', 'nombre', 'codigo', 'tipo', 'tipo_display',
            'comuna', 'lat', 'lng', 'activo'
        ]
