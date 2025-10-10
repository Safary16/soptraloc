# Generated migration for FASE 7: Critical database indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('containers', '0011_merge_20251010_0959'),
    ]

    operations = [
        # Índices para búsquedas frecuentes en Container
        migrations.AddIndex(
            model_name='container',
            index=models.Index(fields=['container_number'], name='container_number_idx'),
        ),
        migrations.AddIndex(
            model_name='container',
            index=models.Index(fields=['status', 'position_status'], name='container_status_idx'),
        ),
        migrations.AddIndex(
            model_name='container',
            index=models.Index(fields=['owner_company', 'status'], name='container_owner_status_idx'),
        ),
        migrations.AddIndex(
            model_name='container',
            index=models.Index(fields=['current_location', 'status'], name='container_location_idx'),
        ),
        migrations.AddIndex(
            model_name='container',
            index=models.Index(fields=['created_at'], name='container_created_idx'),
        ),
        
        # Índices para ContainerMovement
        migrations.AddIndex(
            model_name='containermovement',
            index=models.Index(fields=['container', 'created_at'], name='movement_container_date_idx'),
        ),
        migrations.AddIndex(
            model_name='containermovement',
            index=models.Index(fields=['from_location', 'to_location'], name='movement_locations_idx'),
        ),
        
        # Índices para ContainerInspection
        migrations.AddIndex(
            model_name='containerinspection',
            index=models.Index(fields=['container', 'inspection_date'], name='inspection_container_date_idx'),
        ),
    ]
