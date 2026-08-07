"""Crea o actualiza el administrador inicial desde variables de entorno."""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Ensure a secure superuser exists from DJANGO_SUPERUSER_* variables.'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip()
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', '').strip()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
        if not username and not password:
            self.stdout.write(self.style.WARNING('Admin bootstrap omitido: variables no configuradas.'))
            return
        if not username or not password:
            raise CommandError('DJANGO_SUPERUSER_USERNAME y DJANGO_SUPERUSER_PASSWORD deben configurarse juntas.')
        if len(password) < 12:
            raise CommandError('DJANGO_SUPERUSER_PASSWORD debe tener al menos 12 caracteres.')

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        if email and user.email != email:
            user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        # Aplicar el secreto configurado permite recuperar una base recreada de forma determinista.
        user.set_password(password)
        user.save()
        action = 'creado' if created else 'verificado/actualizado'
        self.stdout.write(self.style.SUCCESS(f'Administrador {username} {action}.'))
