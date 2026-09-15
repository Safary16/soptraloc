import os
import time

import psycopg2
import dj_database_url
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ('Asegura que la base de datos exista: si el servidor responde pero la DB no '
            'existe, la crea (CREATE DATABASE). Reintenta mientras la DB no esté lista.')

    def handle(self, *args, **options):
        url = os.environ.get('DATABASE_URL', '')

        # Local (DEBUG=True) sin DATABASE_URL → SQLite, sin hacer nada.
        if settings.DEBUG and not url:
            self.stdout.write(self.style.SUCCESS('Modo local sin DATABASE_URL: SQLite OK.'))
            return

        # Producción sin DATABASE_URL → fallo claro, no silencio (evita SQLite efímero).
        if not settings.DEBUG and not url:
            self.stdout.write(self.style.ERROR(
                'DATABASE_URL no está definida en producción. '
                'Render no ha provisionado la base de datos.\n'
                'SOLUCIÓN: despliega con el Blueprint render.yaml (New → Blueprint → soptraloc) '
                'para que Render cree el Postgres "soptraloc-db", o crea una PostgreSQL en el '
                'dashboard y pega su connectionString en la env var DATABASE_URL.'))
            raise SystemExit(1)

        parsed = dj_database_url.parse(url)
        host = parsed.get('HOST', 'localhost')
        port = parsed.get('PORT', 5432)
        user = parsed.get('USER', '')
        password = parsed.get('PASSWORD', '')
        dbname = parsed.get('NAME', 'soptraloc')

        retries = int(os.environ.get('DB_STARTUP_MAX_ATTEMPTS', '12'))
        wait = int(os.environ.get('DB_STARTUP_RETRY_SECONDS', '5'))

        for attempt in range(1, retries + 1):
            try:
                conn = psycopg2.connect(
                    host=host, port=port, user=user, password=password,
                    dbname=dbname, connect_timeout=5,
                )
                conn.close()
                self.stdout.write(self.style.SUCCESS(f'Conexión a DB "{dbname}" OK.'))
                return
            except psycopg2.OperationalError as e:
                if 'does not exist' in str(e):
                    # El servidor responde pero la base no existe → forzamos su creación.
                    try:
                        maint = psycopg2.connect(
                            host=host, port=port, user=user, password=password,
                            dbname='postgres', connect_timeout=5,
                        )
                        maint.autocommit = True
                        cur = maint.cursor()
                        cur.execute(f'CREATE DATABASE "{dbname}"')
                        cur.close()
                        maint.close()
                        self.stdout.write(self.style.SUCCESS(f'Base de datos "{dbname}" creada.'))
                        return
                    except Exception as e2:
                        self.stdout.write(self.style.ERROR(
                            f'No se pudo crear la DB "{dbname}": {e2}'))
                        raise SystemExit(1)
                self.stdout.write(self.style.WARNING(
                    f'Intento {attempt}/{retries}: sin conexión a "{host}:{port}" '
                    f'({e}). Reintento en {wait}s...'))
                if attempt < retries:
                    time.sleep(wait)
        self.stdout.write(self.style.ERROR('No se pudo conectar a la base de datos.'))
        raise SystemExit(1)