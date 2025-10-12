from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Driver, DriverLocation


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'user', 'presente', 'activo', 'num_entregas_dia', 'max_entregas_dia', 'cumplimiento_porcentaje', 'ocupacion_display']
    list_filter = ['presente', 'activo']
    search_fields = ['nombre', 'rut', 'telefono', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'total_entregas', 'entregas_a_tiempo', 'ocupacion_display']
    
    fieldsets = (
        ('Usuario del Sistema', {
            'fields': ('user',),
            'description': 'Usuario para acceder al dashboard del conductor. Dejar en blanco para crear uno automáticamente.'
        }),
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
    
    def save_model(self, request, obj, form, change):
        """Crear usuario automáticamente si no existe"""
        if not obj.user and obj.nombre:
            # Generar username desde nombre
            base_username = obj.nombre.lower().replace(' ', '_')
            username = base_username
            counter = 1
            
            # Asegurar que el username sea único
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Crear usuario con password temporal
            password = f"driver{obj.id if obj.id else ''}123"
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=obj.nombre.split()[0] if obj.nombre else '',
                last_name=' '.join(obj.nombre.split()[1:]) if len(obj.nombre.split()) > 1 else ''
            )
            obj.user = user
            messages.success(
                request,
                f'Usuario creado: {username} / Contraseña: {password} (cambiar después del primer login)'
            )
        
        super().save_model(request, obj, form, change)


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ['driver', 'lat', 'lng', 'accuracy', 'timestamp']
    list_filter = ['driver', 'timestamp']
    search_fields = ['driver__nombre']
    readonly_fields = ['driver', 'lat', 'lng', 'accuracy', 'timestamp']
    
    def has_add_permission(self, request):
        return False  # No permitir agregar manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura
