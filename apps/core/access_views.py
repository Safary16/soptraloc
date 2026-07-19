from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods


def role_landing(request):
    """Puerta de entrada única; no decide permisos, solo orienta al portal correcto."""
    return render(request, 'role_landing.html')


@require_http_methods(['GET', 'POST'])
def staff_login(request):
    destination = request.GET.get('next') or request.POST.get('next') or reverse('operations_dashboard')
    if not destination.startswith('/') or destination.startswith('//'):
        destination = reverse('operations_dashboard')
    if request.user.is_authenticated and request.user.is_staff:
        return redirect(destination)
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username', '').strip(),
            password=request.POST.get('password', ''),
        )
        if user and user.is_staff:
            login(request, user)
            return redirect(destination)
        messages.error(request, 'Credenciales inválidas o usuario sin acceso interno.')
    return render(request, 'staff_login.html', {'next': destination})


def staff_logout(request):
    logout(request)
    return redirect('role_landing')


@staff_member_required(login_url='/cuenta/login/')
def control_hub(request):
    """Acceso flexible para carga, liberación y visión global."""
    return render(request, 'control_hub.html')
