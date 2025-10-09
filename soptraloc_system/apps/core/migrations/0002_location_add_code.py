from typing import Optional

from django.db import migrations, models


def build_code_seed(name: Optional[str]) -> str:
    if not name:
        return "LOC"
    cleaned = "".join(ch for ch in name.upper() if ch.isalnum())
    return cleaned[:12] or "LOC"


def add_code_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = "core_location"
    column_name = "code"

    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
                """,
                [table_name, column_name],
            )
            if cursor.fetchone():
                return
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(20)"
            )
        else:  # SQLite, default para entornos de pruebas locales
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if column_name in existing_columns:
                return
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(20)"
            )


def populate_location_codes(apps, schema_editor):
    Location = apps.get_model("drivers", "Location")
    Location._meta.db_table = "core_location"

    for location in Location.objects.all():
        if location.code:
            continue

        base = build_code_seed(location.name)
        candidate = base
        suffix = 1

        while Location.objects.filter(code=candidate).exclude(pk=location.pk).exists():
            suffix += 1
            candidate = f"{base[:10]}{suffix:02d}"

        location.code = candidate
        location.save(update_fields=["code"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("drivers", "0013_fix_location_table"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_code_column, reverse_code=noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="location",
                    name="code",
                    field=models.CharField(
                        max_length=20,
                        unique=False,
                        null=True,
                        blank=True,
                        verbose_name="Código",
                    ),
                ),
            ],
        ),
        migrations.RunPython(populate_location_codes, reverse_code=noop),
        migrations.AlterField(
            model_name="location",
            name="code",
            field=models.CharField(
                max_length=20,
                unique=True,
                null=False,
                blank=False,
                verbose_name="Código",
            ),
        ),
    ]
