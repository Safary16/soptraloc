from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Driver, DriverLocation
import unicodedata


def generar_username(nombre):
    """Genera un username a partir del nombre del conductor"""
    # Normalizar texto (quitar acentos)
    nombre_normalizado = unicodedata.normalize('NFD', nombre)
    nombre_ascii = nombre_normalizado.encode('ascii', 'ignore').decode('utf-8')
    
    # Convertir a minúsculas y reemplazar espacios con guión bajo
    username = nombre_ascii.lower().replace(' ', '_')
    
    # Remover caracteres especiales
    username = ''.join(c for c in username if c.isalnum() or c == '_')
    
    return username


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'rut', 'telefono', 'presente', 'activo',
        'num_entregas_dia', 'max_entregas_dia', 'cumplimiento_porcentaje',
        'tiene_usuario'
    ]
    list_filter = ['activo', 'presente', 'created_at']
    search_fields = ['nombre', 'rut', 'telefono']
    readonly_fields = [
        'ultima_posicion_lat', 'ultima_posicion_lng', 'ultima_actualizacion_posicion',
        'total_entregas', 'entregas_a_tiempo', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'rut', 'telefono', 'user')
        }),
        ('Disponibilidad', {
            'fields': ('presente', 'activo')
        }),
        ('Control de Entregas', {
            'fields': ('num_entregas_dia', 'max_entregas_dia', 'cumplimiento_porcentaje')
        }),
        ('Ubicación GPS', {
            'fields': ('ultima_posicion_lat', 'ultima_posicion_lng', 'ultima_actualizacion_posicion'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('total_entregas', 'entregas_a_tiempo'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tiene_usuario(self, obj):
        """Indica si el conductor tiene usuario asociado"""
        return '✓' if obj.user else '✗'
    tiene_usuario.short_description = 'Usuario'
    
    def save_model(self, request, obj, form, change):
        """Auto-crear usuario cuando se guarda un conductor sin usuario"""
        crear_usuario = False
        
        # Si es un conductor nuevo o existente sin usuario
        if not obj.user:
            crear_usuario = True
        
        # Guardar el conductor primero
        super().save_model(request, obj, form, change)
        
        # Crear usuario si es necesario
        if crear_usuario:
            username = generar_username(obj.nombre)
            password = 'driver123'  # Contraseña por defecto
            
            # Verificar si el username ya existe
            contador = 1
            username_original = username
            while User.objects.filter(username=username).exists():
                username = f"{username_original}_{contador}"
                contador += 1
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=obj.nombre.split()[0] if obj.nombre else '',
                last_name=' '.join(obj.nombre.split()[1:]) if len(obj.nombre.split()) > 1 else ''
            )
            
            # Asociar usuario al conductor
            obj.user = user
            obj.save(update_fields=['user'])
            
            # Mensaje de éxito
            messages.success(
                request,
                f'✓ Usuario creado automáticamente: username: {username} / password: {password}'
            )


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ['driver', 'lat', 'lng', 'accuracy', 'timestamp']
    list_filter = ['driver', 'timestamp']
    search_fields = ['driver__nombre']
    readonly_fields = ['driver', 'lat', 'lng', 'accuracy', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """No permitir agregar ubicaciones manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar ubicaciones"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar ubicaciones antiguas"""
        return True
