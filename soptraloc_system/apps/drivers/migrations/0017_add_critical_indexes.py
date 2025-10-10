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
            index=models.Index(fields=['estado'], name='driver_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='driver',
            index=models.Index(fields=['ubicacion_actual'], name='driver_ubicacion_idx'),
        ),
        
        # Índices para Assignment
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['driver', 'fecha_asignacion'], name='assignment_driver_date_idx'),
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['container', 'estado'], name='assignment_container_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='assignment',
            index=models.Index(fields=['estado', 'fecha_programada'], name='assignment_estado_fecha_idx'),
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
