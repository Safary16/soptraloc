"""
Migración de RESET para tablas de routing en producción.

Estrategia: no tocar estado del modelo en Django; solo ejecutar lógica condicional
para limpiar/recrear tablas en Postgres y crear tablas faltantes si no existen.
"""

from django.db import migrations, connection


def check_if_tables_exist():
    """True si existen tablas básicas de routing en la BD actual."""
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='routing_locationpair';
                """
            )
            row = cursor.fetchone()
            return bool(row and row[0])
        else:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'routing_locationpair'
                );
                """
            )
            row = cursor.fetchone()
            return bool(row and row[0])


def reset_routing_tables(apps, schema_editor):
    """En Postgres: eliminar tablas routing para recrearlas correctamente.
    En SQLite: no hacer nada (mantener tablas locales).
    """
    if connection.vendor != 'postgresql':
        return

    if not check_if_tables_exist():
        return

    with connection.cursor() as cursor:
        for table in [
            'routing_routestop',
            'routing_actualtriprecord',
            'routing_actualoperationrecord',
            'routing_operationtime',
            'routing_locationpair',
            'routing_route',
        ]:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

        # Limpiar historial de migraciones de routing para permitir recreación
        cursor.execute(
            """
            DELETE FROM django_migrations
            WHERE app = 'routing' AND name IN (
                '0001_initial',
                '0002_alter_actualoperationrecord_location_and_more',
                '0003_alter_actualoperationrecord_location_and_more'
            );
            """
        )


def create_routing_tables_if_missing(apps, schema_editor):
    """Crear tablas routing que falten según los modelos actuales."""
    tables_in_db = set(schema_editor.connection.introspection.table_names())
    for app_label, model_name in [
        ("routing", "LocationPair"),
        ("routing", "OperationTime"),
        ("routing", "Route"),
        ("routing", "RouteStop"),
        ("routing", "ActualTripRecord"),
        ("routing", "ActualOperationRecord"),
    ]:
        model = apps.get_model(app_label, model_name)
        table_name = model._meta.db_table
        if table_name not in tables_in_db:
            schema_editor.create_model(model)
            tables_in_db.add(table_name)


def reverse_reset(apps, schema_editor):
    # No-op
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("routing", "0003_alter_actualoperationrecord_location_and_more"),
        ("drivers", "0016_trim_driver_count"),
        ("containers", "0010_alter_container_current_location_and_more"),
    ]

    operations = [
        migrations.RunPython(reset_routing_tables, reverse_reset),
        migrations.RunPython(create_routing_tables_if_missing, migrations.RunPython.noop),
    ]
