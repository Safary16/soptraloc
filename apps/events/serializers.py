from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    container_id = serializers.CharField(source='container.container_id', read_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['created_at']
