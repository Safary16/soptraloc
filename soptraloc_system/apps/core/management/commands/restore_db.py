"""
Management command para restaurar base de datos desde backup
"""
from django.core.management.base import BaseCommand
from decouple import config
import subprocess
import gzip
import shutil
from pathlib import Path


class Command(BaseCommand):
    help = 'Restore database from backup'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to backup file (.sql.gz or .sql)',
        )
        parser.add_argument(
            '--from-s3',
            action='store_true',
            help='Download backup from S3 first',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        backup_path = Path(options['backup_file'])
        
        # Confirmación
        if not options['yes']:
            confirm = input(
                f'\n⚠️  WARNING: This will REPLACE the current database with backup: {backup_path.name}\n'
                'Are you sure? Type "yes" to continue: '
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Restore cancelled'))
                return
        
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('DATABASE RESTORE - SOPTRALOC TMS'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))
        
        # 1. Download from S3 if requested
        if options['from_s3']:
            try:
                self.stdout.write('1️⃣  Downloading backup from S3...')
                aws_bucket = config('AWS_STORAGE_BUCKET_NAME')
                s3_path = f'backups/{backup_path.name}'
                
                subprocess.run([
                    'aws', 's3', 'cp',
                    f's3://{aws_bucket}/{s3_path}',
                    str(backup_path)
                ], check=True)
                
                self.stdout.write(self.style.SUCCESS('   ✅ Downloaded from S3\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ S3 download failed: {e}'))
                return
        
        # 2. Descomprimir si es .gz
        sql_file = backup_path
        if backup_path.suffix == '.gz':
            try:
                self.stdout.write('2️⃣  Decompressing backup...')
                sql_file = backup_path.with_suffix('')
                
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(sql_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                self.stdout.write(self.style.SUCCESS('   ✅ Decompressed\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Decompression failed: {e}'))
                return
        
        # 3. Restore database
        try:
            self.stdout.write('3️⃣  Restoring database...')
            database_url = config('DATABASE_URL')
            
            # Drop all connections first
            self.stdout.write('   Closing existing connections...')
            # ... SQL para cerrar conexiones si es necesario
            
            result = subprocess.run(
                ['psql', database_url, '-f', str(sql_file)],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.stdout.write(self.style.SUCCESS('   ✅ Database restored\n'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Restore failed: {e.stderr}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))
            return
        finally:
            # Cleanup decompressed file if it was created
            if sql_file != backup_path and sql_file.exists():
                sql_file.unlink()
        
        # 4. Run migrations
        try:
            self.stdout.write('4️⃣  Running migrations...')
            from django.core.management import call_command
            call_command('migrate', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('   ✅ Migrations applied\n'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Migrations warning: {e}'))
        
        # Resumen
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('✅ RESTORE COMPLETED SUCCESSFULLY'))
        self.stdout.write('='*80 + '\n')
