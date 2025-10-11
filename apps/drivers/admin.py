from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'presente', 'activo', 'num_entregas_dia', 'max_entregas_dia', 'cumplimiento_porcentaje', 'ocupacion_display']
    list_filter = ['presente', 'activo']
    search_fields = ['nombre', 'rut', 'telefono']
    readonly_fields = ['created_at', 'updated_at', 'total_entregas', 'entregas_a_tiempo', 'ocupacion_display']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'rut', 'telefono')
        }),
        ('Estado', {
            'fields': ('presente', 'activo')
        }),
        ('Capacidad', {
            'fields': ('num_entregas_dia', 'max_entregas_dia')
        }),
        ('Métricas de Desempeño', {
            'fields': ('cumplimiento_porcentaje', 'total_entregas', 'entregas_a_tiempo', 'ocupacion_display')
        }),
        ('Última Posición', {
            'fields': ('ultima_posicion_lat', 'ultima_posicion_lng', 'ultima_actualizacion_posicion'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['resetear_entregas', 'marcar_presente', 'marcar_ausente']
    
    def ocupacion_display(self, obj):
        return f"{obj.ocupacion_porcentaje:.1f}%"
    ocupacion_display.short_description = 'Ocupación'
    
    def resetear_entregas(self, request, queryset):
        for driver in queryset:
            driver.resetear_entregas_dia()
        self.message_user(request, f'Entregas reseteadas para {queryset.count()} conductores.')
    resetear_entregas.short_description = 'Resetear entregas del día'
    
    def marcar_presente(self, request, queryset):
        updated = queryset.update(presente=True)
        self.message_user(request, f'{updated} conductores marcados como presentes.')
    marcar_presente.short_description = 'Marcar como presente'
    
    def marcar_ausente(self, request, queryset):
        updated = queryset.update(presente=False)
        self.message_user(request, f'{updated} conductores marcados como ausentes.')
    marcar_ausente.short_description = 'Marcar como ausente'
