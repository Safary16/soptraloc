"""
Comando para verificar el estado del sistema completo
Útil para debugging y diagnóstico
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from apps.containers.models import Container
from apps.drivers.models import Driver, Alert
from apps.core.models import Company
from apps.drivers.models import Location
import os


class Command(BaseCommand):
    help = 'Verifica el estado completo del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🔍 VERIFICACIÓN DEL SISTEMA SOPTRALOC'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # 1. Configuración
        self.stdout.write('\n📋 CONFIGURACIÓN:')
        self.stdout.write(f'  DEBUG: {settings.DEBUG}')
        self.stdout.write(f'  ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        self.stdout.write(f'  TIME_ZONE: {settings.TIME_ZONE}')
        self.stdout.write(f'  LANGUAGE_CODE: {settings.LANGUAGE_CODE}')
        
        # 2. Base de datos
        self.stdout.write('\n🗄️  BASE DE DATOS:')
        try:
            engine = connection.settings_dict.get('ENGINE', '')
            with connection.cursor() as cursor:
                if 'postgresql' in engine or 'postgis' in engine:
                    cursor.execute("SHOW server_version")
                    version = cursor.fetchone()[0]
                    label = f'PostgreSQL {version}'
                elif 'sqlite' in engine:
                    cursor.execute('SELECT sqlite_version()')
                    version = cursor.fetchone()[0]
                    label = f'SQLite {version}'
                else:
                    cursor.execute('SELECT version()')
                    version = cursor.fetchone()[0]
                    label = version.split(',')[0]

                self.stdout.write(self.style.SUCCESS(f'  ✅ Conectado: {label}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {e}'))
        
        # 3. Modelos y datos
        self.stdout.write('\n📊 DATOS:')
        try:
            containers_count = Container.objects.count()
            drivers_count = Driver.objects.count()
            companies_count = Company.objects.count()
            locations_count = Location.objects.count()
            alerts_count = Alert.objects.filter(is_active=True).count()
            
            self.stdout.write(f'  Contenedores: {containers_count}')
            self.stdout.write(f'  Conductores: {drivers_count}')
            self.stdout.write(f'  Empresas: {companies_count}')
            self.stdout.write(f'  Ubicaciones: {locations_count}')
            self.stdout.write(f'  Alertas activas: {alerts_count}')
            
            if verbose and containers_count > 0:
                # Estadísticas de contenedores
                from django.db.models import Count
                status_stats = Container.objects.values('status').annotate(
                    count=Count('id')
                ).order_by('-count')[:5]
                
                self.stdout.write('\n  📦 Top 5 Estados:')
                for stat in status_stats:
                    self.stdout.write(f'    - {stat["status"]}: {stat["count"]}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error al contar datos: {e}'))
        
        # 4. Archivos estáticos
        self.stdout.write('\n📁 ARCHIVOS ESTÁTICOS:')
        static_root = settings.STATIC_ROOT
        if os.path.exists(static_root):
            file_count = sum(len(files) for _, _, files in os.walk(static_root))
            self.stdout.write(self.style.SUCCESS(f'  ✅ STATIC_ROOT existe: {static_root}'))
            self.stdout.write(f'  Archivos: {file_count}')
        else:
            self.stdout.write(self.style.WARNING(f'  ⚠️  STATIC_ROOT no existe: {static_root}'))
        
        # 5. Apps instaladas
        self.stdout.write('\n🧩 APPS INSTALADAS:')
        local_apps = [app for app in settings.INSTALLED_APPS if app.startswith('apps.')]
        self.stdout.write(f'  Total: {len(settings.INSTALLED_APPS)}')
        self.stdout.write(f'  Apps locales: {len(local_apps)}')
        if verbose:
            for app in local_apps:
                self.stdout.write(f'    - {app}')
        
        # 6. Migraciones pendientes
        self.stdout.write('\n🔄 MIGRACIONES:')
        try:
            from django.core.management import call_command
            from io import StringIO
            
            output = StringIO()
            call_command('showmigrations', '--list', stdout=output)
            migrations_output = output.getvalue()
            
            if '[ ]' in migrations_output:
                self.stdout.write(self.style.WARNING('  ⚠️  Hay migraciones pendientes'))
                if verbose:
                    self.stdout.write(migrations_output)
            else:
                self.stdout.write(self.style.SUCCESS('  ✅ Todas las migraciones aplicadas'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error al verificar migraciones: {e}'))
        
        # Resumen final
        self.stdout.write('\n' + '=' * 70)
        if containers_count > 0 and drivers_count >= 0:
            self.stdout.write(self.style.SUCCESS('✅ SISTEMA OPERATIVO'))
        elif containers_count == 0:
            self.stdout.write(self.style.WARNING('⚠️  SISTEMA SIN DATOS - Usar /setup/ para importar'))
        else:
            self.stdout.write(self.style.ERROR('❌ SISTEMA CON PROBLEMAS'))
        self.stdout.write('=' * 70)
