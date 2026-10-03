"""Data migration: mapea valores viejos 'ccti' → 'patio' en filas existentes.

El rename de conceptos (v0014) solo cambió esquema/choices. Esta migración
convierte valores persistidos para que prod no quede con strings huérfanos:
  - Container.estado: 'en_ccti' → 'en_patio'
  - Container.tipo_movimiento: 'retiro_ccti' → 'retiro_patio'
  - Container.retorno_destino_tipo: 'ccti' → 'patio'
  - Container.fecha_en_ccti → fecha_en_patio: no es valor, es columna (rename en 0014)
"""
from django.db import migrations

MAPS = [
    ('estado', [('en_ccti', 'en_patio')]),
    ('tipo_movimiento', [('retiro_ccti', 'retiro_patio')]),
    ('retorno_destino_tipo', [('ccti', 'patio')]),
]


def forward(apps, schema_editor):
    Container = apps.get_model('containers', 'Container')
    for field, pairs in MAPS:
        for old, new in pairs:
            Container.objects.filter(**{field: old}).update(**{field: new})


def backward(apps, schema_editor):
    Container = apps.get_model('containers', 'Container')
    for field, pairs in MAPS:
        for old, new in pairs:
            Container.objects.filter(**{field: new}).update(**{field: old})


class Migration(migrations.Migration):

    dependencies = [
        ('containers', '0014_remove_container_fecha_en_ccti_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]