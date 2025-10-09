from django.db import migrations


def trim_driver_count(apps, schema_editor):
    Driver = apps.get_model('drivers', 'Driver')
    total = Driver.objects.count()
    if total <= 50:
        return

    keep_ids = list(
        Driver.objects.order_by('created_at').values_list('id', flat=True)[:50]
    )
    Driver.objects.exclude(id__in=keep_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('drivers', '0015_rebuild_location_foreign_keys'),
    ]

    operations = [
        migrations.RunPython(trim_driver_count, migrations.RunPython.noop),
    ]
