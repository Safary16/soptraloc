from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("programaciones", "0010_prog_dashboard_indexes"),
    ]

    operations = [
        # P1-1: fecha real del clic "iniciar descarga" por el conductor.
        # Permite medir la duración real de la descarga (inicio conductor → fin
        # operador) en vez de aproximar con fecha_soltado/fecha_entrega.
        migrations.AddField(
            model_name="programacion",
            name="fecha_inicio_descarga",
            field=models.DateTimeField(
                blank=True,
                help_text=(
                    "Marca real del clic 'iniciar descarga' por el conductor. "
                    "Si existe, se usa como hora_inicio del TiempoOperacion "
                    "descarga_cd (en lugar de fecha_soltado/fecha_entrega)."
                ),
                null=True,
                verbose_name="Fecha Inicio Descarga",
            ),
        ),
        # P1-3: tipo de operación del viaje, default 'viaje' preserva histórico.
        migrations.AddField(
            model_name="tiempoviaje",
            name="tipo_operacion",
            field=models.CharField(
                choices=[
                    ("viaje", "Viaje"),
                    ("retorno_vacio", "Retorno Vacío"),
                ],
                default="viaje",
                help_text="Tipo de viaje para análisis diferenciado (viaje lleno vs retorno vacío).",
                max_length=20,
                verbose_name="Tipo Operación",
            ),
        ),
        # P1-4: nuevos tipos_operacion en TiempoOperacion (carga_ccti, retiro_puerto,
        # devolucion_vacio). Ampliación de choices para que el modelo pueda
        # registrar el ciclo completo del contenedor.
        migrations.AlterField(
            model_name="tiempooperacion",
            name="tipo_operacion",
            field=models.CharField(
                choices=[
                    ("carga_ccti", "Carga en CCTI"),
                    ("descarga_cd", "Descarga en CD"),
                    ("retiro_puerto", "Retiro en Puerto"),
                    ("devolucion_vacio", "Devolución Vacío"),
                ],
                max_length=20,
            ),
        ),
    ]
