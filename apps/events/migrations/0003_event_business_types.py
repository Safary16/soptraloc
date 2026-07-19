from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('events', '0002_alter_event_event_type')]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('import_embarque', 'Importación Embarque'),
                    ('import_liberacion', 'Importación Liberación'),
                    ('import_programacion', 'Importación Programación'),
                    ('asignacion_driver', 'Asignación de Conductor'),
                    ('inicio_ruta', 'Inicio de Ruta'), ('arribo_cd', 'Arribo a CD'),
                    ('llegada_destino', 'Llegada a Destino'),
                    ('contenedor_vacio', 'Contenedor Vacío'),
                    ('contenedor_soltado', 'Contenedor Soltado (Drop & Hook)'),
                    ('devolucion_vacio', 'Devolución Vacío'),
                    ('alerta_48h', 'Alerta 48 Horas'),
                    ('cambio_estado', 'Cambio de Estado'),
                    ('actualizacion_posicion', 'Actualización de Posición'),
                    ('exportacion_stock', 'Exportación de Stock'),
                    ('asignacion_conductor', 'Asignación de Conductor'),
                    ('incidente_reportado', 'Incidente Reportado'),
                ],
                db_index=True, max_length=50, verbose_name='Tipo de Evento',
            ),
        ),
    ]
