"""Complete repair for databases whose migration history exceeds their schema."""
from django.db import migrations


def repair_all_missing_container_columns(apps, schema_editor):
    Container = apps.get_model('containers', 'Container')
    table = Container._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(cursor, table)
        }

    # Concrete local fields include every scalar/FK column Django selects when
    # materializing Container rows. Existing columns and their data are untouched.
    for field in Container._meta.local_fields:
        if field.primary_key:
            continue
        if field.column not in columns:
            schema_editor.add_field(Container, field)
            columns.add(field.column)


class Migration(migrations.Migration):
    dependencies = [('containers', '0009_repair_container_schema_drift')]
    operations = [
        migrations.RunPython(repair_all_missing_container_columns, migrations.RunPython.noop),
    ]
