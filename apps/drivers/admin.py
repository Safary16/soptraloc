from django.contrib import admin, messages

from .access import asegurar_acceso
from .models import Driver, DriverLocation


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'rut', 'telefono', 'presente', 'activo',
        'num_entregas_dia', 'max_entregas_dia', 'cumplimiento_porcentaje',
        'tiene_usuario'
    ]
    list_filter = ['activo', 'presente', 'created_at']
    search_fields = ['nombre', 'rut', 'telefono', 'user__username']
    actions = ['regenerar_acceso']
    readonly_fields = [
        'ultima_posicion_lat', 'ultima_posicion_lng', 'ultima_actualizacion_posicion',
        'total_entregas', 'entregas_a_tiempo', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Información Básica', {'fields': ('nombre', 'rut', 'telefono', 'patente', 'user')}),
        ('Disponibilidad', {'fields': ('presente', 'activo')}),
        ('Control de Entregas', {
            'fields': ('num_entregas_dia', 'max_entregas_dia', 'cumplimiento_porcentaje')
        }),
        ('Ubicación GPS', {
            'fields': ('ultima_posicion_lat', 'ultima_posicion_lng', 'ultima_actualizacion_posicion'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('total_entregas', 'entregas_a_tiempo'), 'classes': ('collapse',)
        }),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Usuario')
    def tiene_usuario(self, obj):
        return obj.user.username if obj.user else 'Sin acceso'

    def save_model(self, request, obj, form, change):
        needs_access = not obj.user_id
        super().save_model(request, obj, form, change)
        if needs_access:
            credentials = asegurar_acceso(obj)
            messages.success(
                request,
                'Acceso temporal (visible una sola vez): '
                f"usuario {credentials['username']} / clave {credentials['temporary_password']}"
            )

    @admin.action(description='Regenerar acceso temporal')
    def regenerar_acceso(self, request, queryset):
        for driver in queryset:
            credentials = asegurar_acceso(driver)
            messages.success(
                request,
                f"{driver.nombre}: {credentials['username']} / {credentials['temporary_password']}"
            )


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ['driver', 'lat', 'lng', 'accuracy', 'timestamp']
    list_filter = ['driver', 'timestamp']
    search_fields = ['driver__nombre']
    readonly_fields = ['driver', 'lat', 'lng', 'accuracy', 'timestamp']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
