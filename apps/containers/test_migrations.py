from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ContainerSchemaDriftRepairTests(TransactionTestCase):
    serialized_rollback = True
    migrate_from = ('containers', '0009_repair_container_schema_drift')
    migrate_to = ('containers', '0010_repair_all_container_columns')

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])

        old_apps = executor.loader.project_state([self.migrate_from]).apps
        Container = old_apps.get_model('containers', 'Container')
        # Simulate drift in both an old (0002) and recent (0008) column.
        with connection.schema_editor() as schema_editor:
            schema_editor.remove_field(Container, Container._meta.get_field('viaje'))
            schema_editor.remove_field(Container, Container._meta.get_field('retorno_destino_tipo'))

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.apps = executor.loader.project_state([self.migrate_to]).apps

    def test_recreates_every_missing_model_column_and_rows_materialize(self):
        Container = self.apps.get_model('containers', 'Container')
        Container.objects.create(container_id='DRFT1234567', tipo='40', nave='Nave')

        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, Container._meta.db_table
                )
            }
        model_columns = {field.column for field in Container._meta.local_fields}
        self.assertTrue(model_columns.issubset(columns))
        self.assertEqual(Container.objects.get(container_id='DRFT1234567').nave, 'Nave')
