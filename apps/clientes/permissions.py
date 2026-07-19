from rest_framework.permissions import BasePermission


class IsClientUser(BasePermission):
    message = 'Se requiere un usuario cliente activo.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and hasattr(request.user, 'perfil_cliente')
            and request.user.perfil_cliente.empresa.activo
        )
