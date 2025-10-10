from django.db import migrations


def _rebuild_table(schema_editor, model, temp_suffix="__old"):
    vendor = schema_editor.connection.vendor
    table_name = model._meta.db_table
    temp_table = f"{table_name}{temp_suffix}"
    qn = schema_editor.quote_name

    if vendor == "sqlite":
        schema_editor.execute("PRAGMA foreign_keys=OFF;")

    schema_editor.execute(f"ALTER TABLE {qn(table_name)} RENAME TO {qn(temp_table)};")
    schema_editor.create_model(model)

    columns = [field.column for field in model._meta.local_fields]
    column_list = ", ".join(qn(column) for column in columns)
    schema_editor.execute(
        f"INSERT INTO {qn(table_name)} ({column_list}) SELECT {column_list} FROM {qn(temp_table)};"
    )
    schema_editor.execute(f"DROP TABLE {qn(temp_table)};")

    pk_column = model._meta.pk.column
    if vendor == "sqlite":
        schema_editor.execute(
            f"UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX({qn(pk_column)}), 0) FROM {qn(table_name)}) WHERE name = '{table_name}';"
        )
        schema_editor.execute("PRAGMA foreign_keys=ON;")


def _list_fk_constraints(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = %s
          AND kcu.column_name = %s
          AND tc.constraint_type = 'FOREIGN KEY'
        """,
        [table_name, column_name],
    )
    return [row[0] for row in cursor.fetchall()]


def _postgres_adjust(schema_editor):
    connection = schema_editor.connection
    tables = {
        "assignments": ["origen_id", "destino_id"],
        "drivers_time_matrix": ["from_location_id", "to_location_id"],
    }

    with connection.cursor() as cursor:
        for table, columns in tables.items():
            for column in columns:
                for constraint in _list_fk_constraints(cursor, table, column):
                    schema_editor.execute(
                        f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint}";'
                    )

                schema_editor.execute(
                    f'ALTER TABLE "{table}" ALTER COLUMN "{column}" TYPE varchar(32) '
                    f'USING "{column}"::text;'
                )

                constraint_name = f"fk_{table}_{column}"
                schema_editor.execute(
                    f'ALTER TABLE "{table}" '
                    f'ADD CONSTRAINT "{constraint_name}" '
                    f'FOREIGN KEY ("{column}") REFERENCES core_location(id) '
                    f'DEFERRABLE INITIALLY DEFERRED;'
                )


def rebuild_driver_relations(apps, schema_editor):
    vendor = schema_editor.connection.vendor

    if vendor == "postgresql":
        _postgres_adjust(schema_editor)
    else:
        Assignment = apps.get_model("drivers", "Assignment")
        TimeMatrix = apps.get_model("drivers", "TimeMatrix")
        _rebuild_table(schema_editor, Assignment)
        _rebuild_table(schema_editor, TimeMatrix)


class Migration(migrations.Migration):

    dependencies = [
        ("drivers", "0014_alter_location_id_alter_location_table"),
        ("containers", "0010_alter_container_current_location_and_more"),
        ("routing", "0003_alter_actualoperationrecord_location_and_more"),
        ("warehouses", "0002_alter_warehouse_location"),
    ]

    operations = [
        migrations.RunPython(rebuild_driver_relations, reverse_code=migrations.RunPython.noop),
    ]
