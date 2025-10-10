"""
Migration para refactorizar Container model sin perder datos.
Crea modelos ContainerSpec, ContainerImportInfo, ContainerSchedule
y migra datos del Container actual.
"""
from django.db import migrations, models
import django.db.models.deletion


def migrate_container_data_forward(apps, schema_editor):
    """Migrar datos de Container a nuevos modelos"""
    Container = apps.get_model('containers', 'Container')
    ContainerSpec = apps.get_model('containers', 'ContainerSpec')
    ContainerImportInfo = apps.get_model('containers', 'ContainerImportInfo')
    ContainerSchedule = apps.get_model('containers', 'ContainerSchedule')
    
    for container in Container.objects.all():
        # ContainerSpec
        ContainerSpec.objects.create(
            container=container,
            weight_empty=container.weight_empty,
            weight_loaded=container.weight_loaded,
            max_weight=container.max_weight,
            seal_number=container.seal_number,
            special_requirements=container.special_requirements
        )
        
        # ContainerImportInfo
        if container.sequence_id or container.vessel_id:
            ContainerImportInfo.objects.create(
                container=container,
                sequence_id=container.sequence_id,
                port=container.port,
                eta=container.eta,
                vessel_id=container.vessel_id,
                cargo_description=container.cargo_description,
                cargo_weight=container.cargo_weight,
                total_weight=container.total_weight,
                terminal_id=container.terminal_id
            )
        
        # ContainerSchedule
        if container.scheduled_date or container.release_date:
            ContainerSchedule.objects.create(
                container=container,
                release_date=container.release_date,
                release_time=container.release_time,
                scheduled_date=container.scheduled_date,
                scheduled_time=container.scheduled_time
            )


def migrate_container_data_reverse(apps, schema_editor):
    """Rollback: copiar datos de vuelta a Container"""
    Container = apps.get_model('containers', 'Container')
    
    for container in Container.objects.all():
        # Restaurar desde ContainerSpec
        if hasattr(container, 'spec'):
            container.weight_empty = container.spec.weight_empty
            container.weight_loaded = container.spec.weight_loaded
            container.max_weight = container.spec.max_weight
            container.seal_number = container.spec.seal_number
            container.special_requirements = container.spec.special_requirements
        
        # Restaurar desde ContainerImportInfo
        if hasattr(container, 'import_info'):
            container.sequence_id = container.import_info.sequence_id
            container.port = container.import_info.port
            container.eta = container.import_info.eta
            container.vessel_id = container.import_info.vessel_id
            container.cargo_description = container.import_info.cargo_description
            container.cargo_weight = container.import_info.cargo_weight
            container.total_weight = container.import_info.total_weight
            container.terminal_id = container.import_info.terminal_id
        
        # Restaurar desde ContainerSchedule
        if hasattr(container, 'schedule'):
            container.release_date = container.schedule.release_date
            container.release_time = container.schedule.release_time
            container.scheduled_date = container.schedule.scheduled_date
            container.scheduled_time = container.schedule.scheduled_time
        
        container.save()


class Migration(migrations.Migration):

    dependencies = [
        ('containers', '0001_initial'),  # Ajustar al número real
    ]

    operations = [
        # ContainerSpec - Especificaciones físicas
        migrations.CreateModel(
            name='ContainerSpec',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('weight_empty', models.DecimalField(blank=True, decimal_places=2, help_text='Peso vacío en kg', max_digits=10, null=True)),
                ('weight_loaded', models.DecimalField(blank=True, decimal_places=2, help_text='Peso cargado en kg', max_digits=10, null=True)),
                ('max_weight', models.DecimalField(blank=True, decimal_places=2, help_text='Peso máximo permitido en kg', max_digits=10, null=True)),
                ('seal_number', models.CharField(blank=True, max_length=50)),
                ('special_requirements', models.TextField(blank=True)),
                ('container', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='spec', to='containers.container')),
            ],
            options={
                'verbose_name': 'Especificación de Contenedor',
                'verbose_name_plural': 'Especificaciones de Contenedores',
            },
        ),
        
        # ContainerImportInfo - Información de importación
        migrations.CreateModel(
            name='ContainerImportInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('sequence_id', models.IntegerField(blank=True, null=True, verbose_name='ID Secuencia')),
                ('port', models.CharField(blank=True, max_length=50, verbose_name='Puerto')),
                ('eta', models.DateField(blank=True, null=True, verbose_name='ETA')),
                ('cargo_description', models.TextField(blank=True, verbose_name='Descripción de carga')),
                ('cargo_weight', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Peso carga')),
                ('total_weight', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Peso total')),
                ('container', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='import_info', to='containers.container')),
                ('terminal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='import_containers', to='drivers.location', verbose_name='Terminal')),
                ('vessel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='containers.vessel', verbose_name='Nave')),
            ],
            options={
                'verbose_name': 'Información de Importación',
                'verbose_name_plural': 'Información de Importaciones',
                'indexes': [
                    models.Index(fields=['sequence_id'], name='containers_seq_idx'),
                    models.Index(fields=['eta'], name='containers_eta_idx'),
                ],
            },
        ),
        
        # ContainerSchedule - Programación y tiempos
        migrations.CreateModel(
            name='ContainerSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('release_date', models.DateField(blank=True, null=True, verbose_name='Fecha liberación')),
                ('release_time', models.TimeField(blank=True, null=True, verbose_name='Hora liberación')),
                ('scheduled_date', models.DateField(blank=True, null=True, verbose_name='Fecha programación')),
                ('scheduled_time', models.TimeField(blank=True, null=True, verbose_name='Hora programación')),
                ('container', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='schedule', to='containers.container')),
            ],
            options={
                'verbose_name': 'Programación de Contenedor',
                'verbose_name_plural': 'Programaciones de Contenedores',
                'indexes': [
                    models.Index(fields=['release_date'], name='containers_rel_date_idx'),
                    models.Index(fields=['scheduled_date'], name='containers_sch_date_idx'),
                ],
            },
        ),
        
        # Migrar datos existentes
        migrations.RunPython(
            migrate_container_data_forward,
            migrate_container_data_reverse
        ),
    ]
