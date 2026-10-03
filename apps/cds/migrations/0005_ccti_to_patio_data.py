"""Data migration: CD.tipo 'ccti' → 'patio' en filas existentes."""
from django.db import migrations


def forward(apps, schema_editor):
    CD = apps.get_model('cds', 'CD')
    CD.objects.filter(tipo='ccti').update(tipo='patio')


def backward(apps, schema_editor):
    CD = apps.get_model('cds', 'CD')
    CD.objects.filter(tipo='patio').update(tipo='ccti')


class Migration(migrations.Migration):

    dependencies = [
        ('cds', '0004_alter_cd_permite_soltar_contenedor_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]