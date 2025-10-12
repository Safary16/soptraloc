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


def importar(request):
    """Vista de importación de archivos Excel"""
    stats = {
        'contenedores': Container.objects.count(),
        'conductores': Driver.objects.count(),
        'cds': CD.objects.count(),
        'programaciones': Programacion.objects.count(),
    }
    return render(request, 'importar.html', {'stats': stats})


def estados(request):
    """Vista de estados de contenedores - ciclo de vida completo"""
    return render(request, 'estados.html')


def container_detail(request, container_id):
    """Vista de detalle de un contenedor específico"""
    from apps.containers.models import Container
    from django.shortcuts import get_object_or_404
    
    container = get_object_or_404(Container, container_id=container_id)
    return render(request, 'container_detail.html', {'container': container})


def containers_list(request):
    """Vista de listado de contenedores con filtros"""
    return render(request, 'containers_list.html')
