"""
Smoke checks de imports y sintaxis.
Este archivo no debe ejecutar side-effects al ser importado por unittest discovery.
"""
import os
import django


def run_import_smoke_checks():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from apps.containers.models import Container  # noqa: F401
    from apps.programaciones.models import Programacion  # noqa: F401
    from apps.cds.models import CD  # noqa: F401
    from apps.drivers.models import Driver  # noqa: F401

    from apps.containers.serializers import ContainerSerializer  # noqa: F401
    from apps.programaciones.serializers import ProgramacionSerializer  # noqa: F401
    from apps.cds.serializers import CDSerializer  # noqa: F401
    from apps.drivers.serializers import DriverSerializer  # noqa: F401

    from apps.containers.views import ContainerViewSet  # noqa: F401
    from apps.programaciones.views import ProgramacionViewSet  # noqa: F401
    from apps.cds.views import CDViewSet  # noqa: F401
    from apps.drivers.views import DriverViewSet  # noqa: F401

    from config.urls import urlpatterns, router  # noqa: F401
    assert len(urlpatterns) > 0
    assert len(router.registry) > 0


if __name__ == '__main__':
    run_import_smoke_checks()
    print("✅ Import smoke checks OK")
