# Generated migration for driver user field and GPS tracking

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('drivers', '0001_initial'),
    ]

    operations = [
        # Add user field to Driver
        migrations.AddField(
            model_name='driver',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='driver',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Usuario'
            ),
        ),
        
        # Create DriverLocation model
        migrations.CreateModel(
            name='DriverLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lat', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Latitud')),
                ('lng', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Longitud')),
                ('accuracy', models.FloatField(blank=True, null=True, verbose_name='Precisión (metros)')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Fecha/Hora')),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ubicaciones', to='drivers.driver', verbose_name='Conductor')),
            ],
            options={
                'verbose_name': 'Ubicación de Conductor',
                'verbose_name_plural': 'Ubicaciones de Conductores',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes for DriverLocation
        migrations.AddIndex(
            model_name='driverlocation',
            index=models.Index(fields=['-timestamp'], name='drivers_dri_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='driverlocation',
            index=models.Index(fields=['driver', '-timestamp'], name='drivers_dri_driver_timesta_idx'),
        ),
    ]
