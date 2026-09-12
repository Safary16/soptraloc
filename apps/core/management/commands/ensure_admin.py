import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

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

        if len(password) < 12:
            self.stdout.write(self.style.ERROR('La contraseña del superusuario debe tener al menos 12 caracteres.'))
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente.'))
        else:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" ya existe. Contraseña y email actualizados.'))
