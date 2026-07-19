"""Repair databases where container migrations were recorded without all columns.

A previous Render deployment could leave django_migrations ahead of the physical
schema.  Keep this migration idempotent so normal databases remain unchanged.
"""
from django.db import migrations


REPAIR_FIELDS = (
    'vacio_contabilizado',
    'fecha_soltado',
    'retorno_destino_tipo',
    'retorno_destino_cd',
)


def repair_missing_container_columns(apps, schema_editor):
    Container = apps.get_model('containers', 'Container')
    table = Container._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(cursor, table)
        }

    for field_name in REPAIR_FIELDS:
        field = Container._meta.get_field(field_name)
        if field.column not in columns:
            schema_editor.add_field(Container, field)
            columns.add(field.column)


class Migration(migrations.Migration):
    dependencies = [
        ('containers', '0008_container_retorno_destino_cd_and_more'),
    ]

    operations = [
        migrations.RunPython(repair_missing_container_columns, migrations.RunPython.noop),
    ]
