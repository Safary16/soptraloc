from rest_framework import serializers

from .models import SolicitudHorario


class SolicitudHorarioSerializer(serializers.ModelSerializer):
    container_id = serializers.CharField(source='container.container_id', read_only=True)
    cd_nombre = serializers.CharField(source='cd.nombre', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    solicitante_nombre = serializers.CharField(source='solicitante.username', read_only=True)

    class Meta:
        model = SolicitudHorario
        fields = (
            'id', 'empresa_nombre', 'container', 'container_id', 'cd', 'cd_nombre',
            'solicitante_nombre', 'modo', 'inicio_solicitado', 'fin_solicitado',
            'recomendacion_snapshot', 'observaciones_cliente', 'estado',
            'inicio_confirmado', 'fin_confirmado', 'respuesta_operaciones',
            'programacion', 'created_at', 'updated_at',
        )
        read_only_fields = fields
