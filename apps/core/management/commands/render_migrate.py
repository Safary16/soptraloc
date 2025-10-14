"""
Management command for safe migrations in Render.com deployment
This command runs migrations with proper logging and error handling
Usage: python manage.py render_migrate
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import sys


class Command(BaseCommand):
    help = 'Run migrations safely for Render.com deployment with logging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what migrations would be applied without applying them',
        )

    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write(self.style.WARNING("🔄 RENDER MIGRATION MANAGER"))
        self.stdout.write("="*60)
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS("✅ Database connection: OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Database connection failed: {e}"))
            sys.exit(1)
        
        # Show pending migrations
        self.stdout.write("\n📋 Checking for pending migrations...")
        try:
            call_command('showmigrations', '--plan')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error showing migrations: {e}"))
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN MODE - No migrations will be applied"))
            sys.exit(0)
        
        # Run migrations
        self.stdout.write("\n🚀 Applying migrations...")
        try:
            call_command('migrate', '--no-input', verbosity=2)
            self.stdout.write(self.style.SUCCESS("\n✅ All migrations applied successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Migration failed: {e}"))
            sys.exit(1)
        
        # Verify models
        self.stdout.write("\n🔍 Running system checks...")
        try:
            call_command('check', '--deploy')
            self.stdout.write(self.style.SUCCESS("✅ System checks passed!"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  System check warnings: {e}"))
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("✅ MIGRATION COMPLETE"))
        self.stdout.write("="*60 + "\n")
