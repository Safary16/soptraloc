import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.drivers.models import Driver

class Command(BaseCommand):
    help = 'Asegura que exista un superusuario basado en variables de entorno'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not all([username, password]):
            self.stdout.write(self.style.WARNING('Variables de entorno DJANGO_SUPERUSER_USERNAME o PASSWORD no definidas. Saltando.'))
            return

        allow_weak = os.environ.get('DJANGO_SUPERUSER_ALLOW_WEAK', '0') in ('1', 'true', 'True', 'yes')
        if len(password) < (4 if allow_weak else 12):
            self.stdout.write(self.style.ERROR(
                'La contraseña del superusuario debe tener al menos '
                f'{"4" if allow_weak else "12"} caracteres '
                '(usa DJANGO_SUPERUSER_ALLOW_WEAK=1 solo en pruebas).'
            ))
            return

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente.'))
        else:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" ya existe. Contraseña y email actualizados.'))

        # Momo: el mismo usuario sirve también para el portal del conductor
        # (login único en todo el sistema: mismo user + misma password).
        if not Driver.objects.filter(user=user).exists():
            Driver.objects.create(
                user=user,
                nombre='Conductor Demo (admin)',
                presente=True,
                activo=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Driver demo vinculado a "{username}" (accede al portal conductor).'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Driver demo ya vinculado a "{username}".'))
