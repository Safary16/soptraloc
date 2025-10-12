"""
Management command to reset admin password easily
Usage: python manage.py reset_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Reset admin password to a default password'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username to reset (default: admin)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='New password (default: admin123)',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password']
        
        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Password reset successfully!\n'
                    f'   Username: {username}\n'
                    f'   Password: {password}\n'
                    f'   URL: http://localhost:8000/admin/\n'
                )
            )
        except User.DoesNotExist:
            # Create new admin user
            user = User.objects.create_superuser(
                username=username,
                email=f'{username}@soptraloc.cl',
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Admin user created successfully!\n'
                    f'   Username: {username}\n'
                    f'   Password: {password}\n'
                    f'   URL: http://localhost:8000/admin/\n'
                )
            )
