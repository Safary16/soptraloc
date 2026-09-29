"""Pobla el catálogo Deposit con los valores existentes en
Container.deposito_devolucion (texto libre) y linkea por match exacto de
nombre. Genérico: no asume ningún depósito ni cliente en particular.
"""
from django.db import migrations


def crear_depositos_desde_contenedores(apps, schema_editor):
    Container = apps.get_model('containers', 'Container')
    Deposit = apps.get_model('containers', 'Deposit')
    for valor in (
        Container.objects.exclude(deposito_devolucion=None)
        .exclude(deposito_devolucion='')
        .values_list('deposito_devolucion', flat=True)
        .distinct()
    ):
        nombre = str(valor).strip()
        if not nombre:
            continue
        Deposit.objects.get_or_create(
            name=nombre, defaults={'activo': True}
        )


def borrar_depositos_creados(apps, schema_editor):
    Deposit = apps.get_model('containers', 'Deposit')
    Deposit.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('containers', '0012_deposit_container_estado_verificado_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_depositos_desde_contenedores, borrar_depositos_creados),
    ]
