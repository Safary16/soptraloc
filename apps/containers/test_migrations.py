from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ContainerSchemaDriftRepairTests(TransactionTestCase):
    serialized_rollback = True
    migrate_from = ('containers', '0008_container_retorno_destino_cd_and_more')
    migrate_to = ('containers', '0009_repair_container_schema_drift')

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])

        old_apps = executor.loader.project_state([self.migrate_from]).apps
        Container = old_apps.get_model('containers', 'Container')
        field = Container._meta.get_field('fecha_soltado')
        with connection.schema_editor() as schema_editor:
            schema_editor.remove_field(Container, field)

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.apps = executor.loader.project_state([self.migrate_to]).apps

    def test_recreates_missing_column_without_losing_rows(self):
        Container = self.apps.get_model('containers', 'Container')
        Container.objects.create(container_id='DRFT1234567', tipo='40', nave='Nave')

        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                connection.cursor(), Container._meta.db_table
            )
        }
        self.assertIn('fecha_soltado', columns)
        self.assertEqual(Container.objects.get(container_id='DRFT1234567').nave, 'Nave')
