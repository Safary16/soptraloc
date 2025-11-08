from rest_framework import serializers
from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer completo para notificaciones"""
    
    container_id = serializers.CharField(source='container.container_id', read_only=True)
    container_id_formatted = serializers.CharField(source='container.container_id_formatted', read_only=True)
    driver_nombre = serializers.CharField(source='driver.nombre', read_only=True, allow_null=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiempo_desde_creacion = serializers.IntegerField(read_only=True)
    es_reciente = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'container', 'container_id', 'container_id_formatted', 'driver', 'driver_nombre',
            'programacion', 'tipo', 'tipo_display', 'prioridad', 'prioridad_display',
            'estado', 'estado_display', 'titulo', 'mensaje', 'eta_minutos',
            'eta_timestamp', 'distancia_km', 'lat_actual', 'lng_actual',
            'detalles', 'created_at', 'enviada_at', 'leida_at',
            'tiempo_desde_creacion', 'es_reciente'
        ]
        read_only_fields = [
            'created_at', 'enviada_at', 'leida_at', 'tiempo_desde_creacion', 'es_reciente'
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    
    container_id = serializers.CharField(source='container.container_id', read_only=True)
    container_id_formatted = serializers.CharField(source='container.container_id_formatted', read_only=True)
    driver_nombre = serializers.CharField(source='driver.nombre', read_only=True, allow_null=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'container_id', 'container_id_formatted', 'driver_nombre', 'tipo', 'tipo_display',
            'prioridad', 'prioridad_display', 'estado', 'titulo', 'mensaje',
            'eta_minutos', 'eta_timestamp', 'created_at'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer para preferencias de notificación"""
    
    canal_display = serializers.CharField(source='get_canal_display', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'usuario', 'canal', 'canal_display', 'activo',
            'tipos_notificacion', 'email_destino', 'telefono_destino',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
