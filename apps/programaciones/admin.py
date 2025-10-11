from django.contrib import admin
from .models import Programacion


@admin.register(Programacion)
class ProgramacionAdmin(admin.ModelAdmin):
    list_display = ['container', 'fecha_programada', 'cliente', 'cd', 'driver', 'requiere_alerta', 'horas_restantes']
    list_filter = ['fecha_programada', 'requiere_alerta', 'alerta_48h_enviada', 'cd']
    search_fields = ['container__container_id', 'cliente', 'driver__nombre']
    readonly_fields = ['created_at', 'updated_at', 'horas_restantes', 'requiere_conductor_urgente']
    autocomplete_fields = ['container', 'driver', 'cd']
    
    fieldsets = (
        ('Contenedor y Destino', {
            'fields': ('container', 'cd', 'cliente', 'direccion_entrega')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'driver')
        }),
        ('Datos de Ruta (Mapbox)', {
            'fields': ('eta_minutos', 'distancia_km', 'ruta_geojson'),
            'classes': ('collapse',)
        }),
        ('Alertas', {
            'fields': ('requiere_alerta', 'alerta_48h_enviada', 'horas_restantes', 'requiere_conductor_urgente')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def horas_restantes(self, obj):
        horas = obj.horas_hasta_programacion
        if horas is None:
            return "-"
        if horas < 0:
            return f"Venció hace {abs(horas):.1f}h"
        return f"{horas:.1f}h"
    horas_restantes.short_description = 'Tiempo Restante'
