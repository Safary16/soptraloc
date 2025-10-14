# Generated migration for adding patente field to Driver model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drivers', '0003_rename_drivers_dri_timesta_idx_drivers_dri_timesta_eb0b05_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='patente',
            field=models.CharField(blank=True, help_text='Patente del vehículo asignado', max_length=20, null=True, verbose_name='Patente'),
        ),
    ]
