from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('containers', '0005_add_excel_fields')]

    operations = [
        migrations.AddField(
            model_name='container',
            name='vacio_contabilizado',
            field=models.BooleanField(
                default=False,
                help_text='Evita incrementar más de una vez el inventario de vacíos del CD.',
                verbose_name='Vacío contabilizado en CD',
            ),
        ),
        migrations.AlterField(
            model_name='container',
            name='estado',
            field=models.CharField(
                choices=[
                    ('por_arribar', 'Por Arribar'), ('liberado', 'Liberado'),
                    ('secuenciado', 'Secuenciado'), ('programado', 'Programado'),
                    ('asignado', 'Asignado'), ('en_ruta', 'En Ruta'),
                    ('entregado', 'Entregado'), ('descargado', 'Descargado'),
                    ('vacio', 'Vacío'), ('vacio_en_ruta', 'Vacío en Ruta'),
                    ('devuelto', 'Devuelto'), ('cancelado', 'Cancelado'),
                    ('incidente', 'Incidente'),
                ],
                db_index=True, default='por_arribar', max_length=20,
                verbose_name='Estado',
            ),
        ),
    ]
