"""
Sistema de permisos granulares (RBAC) para SOPTRALOC TMS.
FASE 6: Seguridad - Role-Based Access Control.
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permiso para usuarios administradores.
    Tienen acceso total al sistema.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.is_staff
        )


class IsOperatorUser(permissions.BasePermission):
    """
    Permiso para usuarios operadores.
    Pueden crear, actualizar y ver datos operacionales.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y staff tienen todos los permisos
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Operadores pueden ver, crear y actualizar (no eliminar)
        if request.method in ['GET', 'POST', 'PUT', 'PATCH']:
            return hasattr(request.user, 'role') and request.user.role == 'operator'
        
        return False


class IsViewerUser(permissions.BasePermission):
    """
    Permiso para usuarios con rol de solo lectura.
    Solo pueden ver datos, no modificar.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y staff tienen todos los permisos
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Viewers solo pueden usar métodos seguros (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class CanManageContainers(permissions.BasePermission):
    """
    Permiso específico para gestión de contenedores.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin puede todo
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Solo lectura para todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Modificación solo para operadores y admin
        return hasattr(request.user, 'role') and request.user.role in ['operator', 'admin']
    
    def has_object_permission(self, request, view, obj):
        """
        Permisos a nivel de objeto.
        Los usuarios solo pueden modificar contenedores de su empresa.
        """
        # Admin puede todo
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Solo lectura siempre permitida
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Verificar que el contenedor pertenece a la empresa del usuario
        if hasattr(request.user, 'company'):
            return obj.owner_company == request.user.company or obj.client == request.user.company
        
        return False


class CanManageDrivers(permissions.BasePermission):
    """
    Permiso específico para gestión de conductores.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin puede todo
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Solo lectura para todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Modificación solo para operadores y admin
        return hasattr(request.user, 'role') and request.user.role in ['operator', 'admin']


class CanAssignContainers(permissions.BasePermission):
    """
    Permiso para asignar contenedores a conductores.
    Solo admin y operadores.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y staff pueden asignar
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Solo operadores y admin pueden asignar
        return hasattr(request.user, 'role') and request.user.role in ['operator', 'admin']


class CanImportData(permissions.BasePermission):
    """
    Permiso para importar datos desde Excel.
    Solo admin y operadores con permisos especiales.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin siempre puede importar
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Operadores con permiso específico
        if hasattr(request.user, 'role') and request.user.role == 'operator':
            return hasattr(request.user, 'can_import_data') and request.user.can_import_data
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso de objeto personalizado: solo el creador puede editar.
    Los demás pueden solo leer.
    """
    
    def has_object_permission(self, request, view, obj):
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin puede todo
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Escritura solo para el creador
        return obj.created_by == request.user


# Composición de permisos por ViewSet
class ContainerPermissions:
    """Permisos compuestos para ContainerViewSet."""
    permission_classes = [
        permissions.IsAuthenticated,
        CanManageContainers
    ]


class DriverPermissions:
    """Permisos compuestos para DriverViewSet."""
    permission_classes = [
        permissions.IsAuthenticated,
        CanManageDrivers
    ]


class AssignmentPermissions:
    """Permisos compuestos para operaciones de asignación."""
    permission_classes = [
        permissions.IsAuthenticated,
        CanAssignContainers
    ]


class ImportPermissions:
    """Permisos compuestos para importación de datos."""
    permission_classes = [
        permissions.IsAuthenticated,
        CanImportData
    ]


# Función helper para verificar roles
def has_role(user, role):
    """
    Verifica si un usuario tiene un rol específico.
    
    Args:
        user: Usuario de Django
        role: Rol a verificar ('admin', 'operator', 'viewer')
    
    Returns:
        bool: True si el usuario tiene el rol
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    if user.is_staff and role in ['admin', 'operator', 'viewer']:
        return True
    
    return hasattr(user, 'role') and user.role == role
