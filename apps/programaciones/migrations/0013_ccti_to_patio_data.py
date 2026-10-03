"""Data migration: TiempoOperacion.tipo_operacion 'carga_ccti' → 'carga_patio'."""
from django.db import migrations


def forward(apps, schema_editor):
    TiempoOperacion = apps.get_model('programaciones', 'TiempoOperacion')
    TiempoOperacion.objects.filter(tipo_operacion='carga_ccti').update(tipo_operacion='carga_patio')


def backward(apps, schema_editor):
    TiempoOperacion = apps.get_model('programaciones', 'TiempoOperacion')
    TiempoOperacion.objects.filter(tipo_operacion='carga_patio').update(tipo_operacion='carga_ccti')


class Migration(migrations.Migration):

    dependencies = [
        ('programaciones', '0012_alter_tiempooperacion_tipo_operacion'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]