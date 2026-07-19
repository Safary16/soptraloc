import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('clientes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SituacionCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('categoria', models.CharField(choices=[('operativa', 'Situación operativa'), ('documental', 'Documentación'), ('stock', 'Diferencia de stock'), ('horario', 'Horario o recepción'), ('otro', 'Otro')], default='operativa', max_length=20)),
                ('prioridad', models.CharField(choices=[('normal', 'Normal'), ('alta', 'Alta'), ('urgente', 'Urgente')], default='normal', max_length=10)),
                ('asunto', models.CharField(max_length=160)),
                ('mensaje', models.TextField()),
                ('estado', models.CharField(choices=[('abierta', 'Abierta'), ('en_revision', 'En revisión'), ('resuelta', 'Resuelta'), ('cerrada', 'Cerrada')], db_index=True, default='abierta', max_length=15)),
                ('respuesta_operaciones', models.TextField(blank=True)),
                ('revisada_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('container', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='situaciones_cliente', to='containers.container')),
                ('creada_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='situaciones_cliente', to=settings.AUTH_USER_MODEL)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='situaciones', to='clientes.clienteempresa')),
                ('revisada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='situaciones_cliente_revisadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='situacioncliente',
            index=models.Index(fields=['empresa', 'estado', 'prioridad'], name='clientes_si_empresa_e06fb4_idx'),
        ),
    ]
