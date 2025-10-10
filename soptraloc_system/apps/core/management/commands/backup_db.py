"""
Management command para hacer backup de la base de datos y subirlo a S3
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config
import subprocess
import os
import gzip
import shutil
from datetime import datetime
from pathlib import Path


class Command(BaseCommand):
    help = 'Backup database to S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--local-only',
            action='store_true',
            help='Only create local backup without uploading to S3',
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=7,
            help='Number of days to keep backups (default: 7)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('DATABASE BACKUP - SOPTRALOC TMS'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))
        
        # 1. Crear directorio de backups
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_folder = datetime.now().strftime('%Y-%m-%d')
        backup_file = backup_dir / f'soptraloc_backup_{timestamp}.sql'
        backup_file_gz = backup_dir / f'soptraloc_backup_{timestamp}.sql.gz'
        
        # 2. Obtener DATABASE_URL
        database_url = config('DATABASE_URL', default=None)
        if not database_url:
            self.stdout.write(self.style.ERROR('❌ DATABASE_URL not configured'))
            return
        
        # 3. Dump database
        try:
            self.stdout.write('1️⃣  Dumping database...')
            result = subprocess.run(
                ['pg_dump', database_url, '-f', str(backup_file)],
                capture_output=True,
                text=True,
                check=True
            )
            file_size_mb = backup_file.stat().st_size / (1024 * 1024)
            self.stdout.write(self.style.SUCCESS(
                f'   ✅ Database dumped: {backup_file.name} ({file_size_mb:.2f} MB)\n'
            ))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'   ❌ pg_dump failed: {e.stderr}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))
            return
        
        # 4. Comprimir backup
        try:
            self.stdout.write('2️⃣  Compressing backup...')
            with open(backup_file, 'rb') as f_in:
                with gzip.open(backup_file_gz, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            compressed_size_mb = backup_file_gz.stat().st_size / (1024 * 1024)
            compression_ratio = (1 - compressed_size_mb / file_size_mb) * 100
            
            # Eliminar archivo sin comprimir
            backup_file.unlink()
            
            self.stdout.write(self.style.SUCCESS(
                f'   ✅ Compressed: {backup_file_gz.name} ({compressed_size_mb:.2f} MB, '
                f'{compression_ratio:.1f}% reduction)\n'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Compression failed: {str(e)}'))
            return
        
        # 5. Upload to S3 (si no es local-only)
        if not options['local_only']:
            try:
                aws_access_key = config('AWS_ACCESS_KEY_ID', default=None)
                aws_secret_key = config('AWS_SECRET_ACCESS_KEY', default=None)
                aws_bucket = config('AWS_STORAGE_BUCKET_NAME', default=None)
                
                if not all([aws_access_key, aws_secret_key, aws_bucket]):
                    self.stdout.write(self.style.WARNING(
                        '   ⚠️  AWS credentials not configured, skipping S3 upload'
                    ))
                else:
                    self.stdout.write('3️⃣  Uploading to S3...')
                    s3_path = f'backups/{date_folder}/{backup_file_gz.name}'
                    
                    subprocess.run([
                        'aws', 's3', 'cp',
                        str(backup_file_gz),
                        f's3://{aws_bucket}/{s3_path}'
                    ], check=True, env={
                        **os.environ,
                        'AWS_ACCESS_KEY_ID': aws_access_key,
                        'AWS_SECRET_ACCESS_KEY': aws_secret_key
                    })
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✅ Uploaded to S3: s3://{aws_bucket}/{s3_path}\n'
                    ))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.WARNING(
                    f'   ⚠️  S3 upload failed (backup still saved locally): {e}'
                ))
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'   ⚠️  S3 upload error: {str(e)}'
                ))
        
        # 6. Cleanup old backups
        try:
            self.stdout.write(f'4️⃣  Cleaning old backups (>{options["keep_days"]} days)...')
            import time
            cutoff_time = time.time() - (options['keep_days'] * 86400)
            deleted_count = 0
            
            for old_backup in backup_dir.glob('soptraloc_backup_*.sql.gz'):
                if old_backup.stat().st_mtime < cutoff_time:
                    old_backup.unlink()
                    deleted_count += 1
            
            remaining = len(list(backup_dir.glob('soptraloc_backup_*.sql.gz')))
            self.stdout.write(self.style.SUCCESS(
                f'   ✅ Deleted {deleted_count} old backups, {remaining} remaining\n'
            ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  Cleanup failed: {str(e)}'
            ))
        
        # Resumen
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('✅ BACKUP COMPLETED SUCCESSFULLY'))
        self.stdout.write('='*80)
        self.stdout.write(f'Backup file: {backup_file_gz}')
        self.stdout.write(f'Size: {compressed_size_mb:.2f} MB')
        self.stdout.write(f'Timestamp: {timestamp}')
        self.stdout.write('='*80 + '\n')
