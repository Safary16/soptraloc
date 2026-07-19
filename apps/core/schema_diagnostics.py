from django.apps import apps
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def schema_read_diagnostics(request):
    """Temporary, value-free probe for production schema/data read failures."""
    targets = ('containers.Container', 'cds.CD', 'programaciones.Programacion')
    result = {}
    for label in targets:
        model = apps.get_model(label)
        model_result = {'count': None, 'broken_fields': []}
        try:
            model_result['count'] = model.objects.count()
        except Exception as exc:
            model_result['count_error'] = type(exc).__name__
        for field in model._meta.local_fields:
            try:
                list(model.objects.values_list(field.attname, flat=True)[:1])
            except Exception as exc:
                model_result['broken_fields'].append({
                    'field': field.name,
                    'column': field.column,
                    'error': type(exc).__name__,
                })
        result[label] = model_result
    return JsonResponse({'database_vendor': connection.vendor, 'models': result})
