# Generated migration for FASE 7: Driver and Assignment indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drivers', '0016_trim_driver_count'),
    ]

    operations = [
        # Índices para Driver
        migrations.AddIndex(
            model_name='driver',
            index=models.Index(fields=['rut'], name='driver_rut_idx'),
        ),
        migrations.AddIndex(
            model_name='driver',
            index=models.Index(fields=['status'], name='driver_status_idx'),
        ),
        migrations.AddIndex(
            model_name='driver',
            index=models.Index(fields=['current_location'], name='driver_location_idx'),
        ),
        
        # Índices para Assignment
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['driver', 'assignment_date'], name='assignment_driver_date_idx'),
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['container', 'status'], name='assignment_container_status_idx'),
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['status', 'assignment_date'], name='assignment_status_date_idx'),
        ),
        
        # Índices para Location
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['name'], name='location_name_idx'),
        ),
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['code'], name='location_code_idx'),
        ),
    ]
