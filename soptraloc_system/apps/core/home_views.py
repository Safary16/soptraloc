from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.containers.models import Container
from apps.core.models import Company
from apps.drivers.models import Driver, Location


class HomeView(TemplateView):
    """Vista principal del sistema SOPTRALOC."""
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'SOPTRALOC - Sistema de Optimización de Transporte',
            'total_containers': Container.objects.count(),
            'total_companies': Company.objects.count(),
            'total_drivers': Driver.objects.count(),
        })
        return context


def health_check(request):
    """Health check endpoint para monitoreo del sistema."""
    return JsonResponse({
        'status': 'ok',
        'service': 'soptraloc',
        'version': '1.0.0',
        'timestamp': '2025-09-28T15:35:00Z'
    })


def api_info(request):
    """Información de la API."""
    return JsonResponse({
        'name': 'SOPTRALOC API',
        'version': 'v1',
        'description': 'Sistema de optimización para transporte de contenedores',
        'endpoints': {
            'admin': '/admin/',
            'api_core': '/api/v1/core/',
            'api_containers': '/api/v1/containers/',
            'swagger': '/swagger/',
            'redoc': '/redoc/',
        }
    })