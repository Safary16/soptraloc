from django.contrib import admin
from .models import Container


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ['container_id', 'tipo', 'estado', 'nave', 'posicion_fisica', 'comuna', 'secuenciado', 'updated_at']
    list_filter = ['estado', 'tipo', 'secuenciado', 'puerto']
    search_fields = ['container_id', 'nave', 'vendor', 'sello', 'comuna']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('container_id', 'tipo', 'nave')
        }),
        ('Detalles del Embarque', {
            'fields': ('peso', 'vendor', 'sello', 'puerto')
        }),
        ('Estado y Ubicación', {
            'fields': ('estado', 'posicion_fisica', 'comuna', 'secuenciado')
        }),
        ('Timestamps', {
            'fields': (
                'fecha_arribo', 'fecha_liberacion', 'fecha_programacion',
                'fecha_asignacion', 'fecha_inicio_ruta', 'fecha_entrega'
            )
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_secuenciado', 'desmarcar_secuenciado']
    
    def marcar_secuenciado(self, request, queryset):
        updated = queryset.update(secuenciado=True)
        self.message_user(request, f'{updated} contenedores marcados como secuenciados.')
    marcar_secuenciado.short_description = 'Marcar como secuenciado'
    
    def desmarcar_secuenciado(self, request, queryset):
        updated = queryset.update(secuenciado=False)
        self.message_user(request, f'{updated} contenedores desmarcados como secuenciados.')
    desmarcar_secuenciado.short_description = 'Desmarcar secuenciado'
