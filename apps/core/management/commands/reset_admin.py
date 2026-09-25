"""
Management command to reset admin password easily
Usage: python manage.py reset_admin [--username admin] [--password <nueva>]

Por seguridad, la contraseña NUNCA se imprime en stdout. Si se omite
--password y el usuario no existe aún, se usa el fallback FALLBACK_PASSWORD
interno (no se imprime); si se entrega por --password, queda registrada
en el secreto que se pasa al comando (shell history) — pero no se loguea.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

FALLBACK_PASSWORD = 'admin123'


class Command(BaseCommand):
    help = 'Reset admin password to a default password (never prints password to stdout)'

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
            default=None,
            help=(
                'New password. If omitted, uses DJANGO_SUPERUSER_PASSWORD env var '
                f'or internal fallback (never printed).'
            ),
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password'] or os.environ.get('DJANGO_SUPERUSER_PASSWORD') or FALLBACK_PASSWORD

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
                    f'   Password: <not printed for security> '
                    f'(use DJANGO_SUPERUSER_PASSWORD or pass --password to set it).\n'
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
                    f'   Password: <not printed for security> '
                    f'(use DJANGO_SUPERUSER_PASSWORD or pass --password to set it).\n'
                    f'   URL: http://localhost:8000/admin/\n'
                )
            )
