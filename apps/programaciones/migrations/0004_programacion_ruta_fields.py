# Generated migration for adding route tracking fields to Programacion model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programaciones', '0003_programacion_fecha_asignacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='programacion',
            name='patente_confirmada',
            field=models.CharField(blank=True, help_text='Patente confirmada al iniciar ruta', max_length=20, null=True, verbose_name='Patente Confirmada'),
        ),
        migrations.AddField(
            model_name='programacion',
            name='fecha_inicio_ruta',
            field=models.DateTimeField(blank=True, help_text='Timestamp cuando el conductor inició la ruta', null=True, verbose_name='Fecha Inicio Ruta'),
        ),
        migrations.AddField(
            model_name='programacion',
            name='gps_inicio_lat',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='GPS Inicio Latitud'),
        ),
        migrations.AddField(
            model_name='programacion',
            name='gps_inicio_lng',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='GPS Inicio Longitud'),
        ),
    ]
