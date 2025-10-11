from django.shortcuts import render
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD
from apps.programaciones.models import Programacion


def home(request):
    """Vista principal del dashboard"""
    stats = {
        'contenedores': Container.objects.count(),
        'conductores': Driver.objects.count(),
        'cds': CD.objects.count(),
        'programaciones': Programacion.objects.count(),
    }
    return render(request, 'home.html', {'stats': stats})


def asignacion(request):
    """Vista de asignación de conductores"""
    return render(request, 'asignacion.html')
