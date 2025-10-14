"""
Management command for maintenance tasks in Render.com deployment
This command handles cleanup, optimization, and routine maintenance
Usage: python manage.py render_maintenance
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from django.db import transaction
from datetime import timedelta


class Command(BaseCommand):
    help = 'Run maintenance tasks for Render.com deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup-old-data',
            action='store_true',
            help='Clean up old GPS tracking data (older than 30 days)',
        )
        parser.add_argument(
            '--cleanup-sessions',
            action='store_true',
            help='Clean up expired sessions',
        )
        parser.add_argument(
            '--optimize-db',
            action='store_true',
            help='Optimize database (VACUUM on PostgreSQL)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all maintenance tasks',
        )

    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write(self.style.WARNING("🔧 RENDER MAINTENANCE MANAGER"))
        self.stdout.write("="*60)
        
        run_all = options['all']
        
        # Clean up old GPS data
        if options['cleanup_old_data'] or run_all:
            self.stdout.write("\n🗑️  Cleaning old GPS tracking data...")
            self._cleanup_old_gps_data()
        
        # Clean up expired sessions
        if options['cleanup_sessions'] or run_all:
            self.stdout.write("\n🗑️  Cleaning expired sessions...")
            self._cleanup_sessions()
        
        # Optimize database
        if options['optimize_db'] or run_all:
            self.stdout.write("\n⚡ Optimizing database...")
            self._optimize_database()
        
        if not any([options['cleanup_old_data'], options['cleanup_sessions'], 
                    options['optimize_db'], run_all]):
            self.stdout.write(self.style.WARNING("\n⚠️  No maintenance task specified."))
            self.stdout.write("Use --all to run all tasks or specify individual tasks:")
            self.stdout.write("  --cleanup-old-data")
            self.stdout.write("  --cleanup-sessions")
            self.stdout.write("  --optimize-db")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("✅ MAINTENANCE COMPLETE"))
        self.stdout.write("="*60 + "\n")

    def _cleanup_old_gps_data(self):
        """Clean up GPS tracking data older than 30 days"""
        try:
            from apps.drivers.models import Driver
            
            cutoff_date = timezone.now() - timedelta(days=30)
            
            # Clear old GPS positions from drivers
            with transaction.atomic():
                drivers_updated = Driver.objects.filter(
                    ultima_actualizacion_gps__lt=cutoff_date
                ).update(
                    ultima_posicion_lat=None,
                    ultima_posicion_lng=None
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Cleaned GPS data from {drivers_updated} drivers (older than 30 days)"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error cleaning GPS data: {e}")
            )

    def _cleanup_sessions(self):
        """Clean up expired sessions"""
        try:
            call_command('clearsessions')
            self.stdout.write(self.style.SUCCESS("✅ Expired sessions cleaned"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error cleaning sessions: {e}")
            )

    def _optimize_database(self):
        """Optimize database (PostgreSQL VACUUM)"""
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Check if PostgreSQL
                if connection.vendor == 'postgresql':
                    self.stdout.write("Running VACUUM ANALYZE...")
                    cursor.execute("VACUUM ANALYZE")
                    self.stdout.write(
                        self.style.SUCCESS("✅ Database optimized (VACUUM ANALYZE)")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️  Database optimization only available for PostgreSQL")
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error optimizing database: {e}")
            )
