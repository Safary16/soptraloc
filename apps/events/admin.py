from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'event_type', 'container', 'usuario']
    list_filter = ['event_type', 'created_at']
    search_fields = ['container__container_id', 'usuario']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Evento', {
            'fields': ('container', 'event_type', 'usuario')
        }),
        ('Detalles', {
            'fields': ('detalles',)
        }),
        ('Fecha', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        # Los eventos solo se crean automáticamente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Los eventos no se pueden modificar
        return False
