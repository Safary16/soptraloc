import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.drivers.models import Driver

# Credenciales por defecto de prueba (periodo de pruebas; se documentan en render.yaml).
# Si las variables de entorno no existen (ej: servicio creado desde UI sin Blueprint),
# el arranque SIEMPRE garantiza admin/1234 para poder operar el sistema.
FALLBACK_USERNAME = 'admin'
FALLBACK_EMAIL = 'admin@soptraloc.cl'
FALLBACK_PASSWORD = '1234'


class Command(BaseCommand):
    help = 'Asegura que exista un superusuario (admin/1234 por defecto) y su driver vinculado'

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME') or FALLBACK_USERNAME
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL') or FALLBACK_EMAIL
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD') or FALLBACK_PASSWORD

        allow_weak = os.environ.get('DJANGO_SUPERUSER_ALLOW_WEAK', '1') in ('1', 'true', 'True', 'yes')
        # Longitud mínima configurable: en desarrollo (DJANGO_SUPERUSER_ALLOW_WEAK=1)
        # aceptamos el fallback admin/1234; en producción exigimos al menos 12 chars.
        min_len = 4 if allow_weak else 12
        if len(password) < min_len:
            self.stdout.write(self.style.ERROR(
                f'La contraseña del superusuario debe tener al menos {min_len} caracteres '
                '(usa DJANGO_SUPERUSER_ALLOW_WEAK=1 solo en pruebas).'
            ))
            return

        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente.'))
        else:
            # Garantizar que sea activo, staff y superusuario, con la clave de entorno/fallback
            user.set_password(password)
            user.email = email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'Superusuario "{username}" actualizado (activo/staff/superuser, clave reseteada).'))

        # Vinculamos un Driver al mismo usuario para que admin/1234 sirva también
        # en el portal del conductor (login único en todo el sistema).
        driver = Driver.objects.filter(user=user).first()
        if driver is None:
            Driver.objects.create(
                user=user,
                nombre='Conductor Demo (admin)',
                presente=True,
                activo=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Driver demo vinculado a "{username}" (accede al portal conductor).'))
        else:
            driver.activo = True
            driver.presente = True
            driver.save()
            self.stdout.write(self.style.SUCCESS(f'Driver demo ya vinculado a "{username}" (reactivado).'))

        # NUNCA imprimir la contraseña real en stdout/logs: si el usuario la olvidó,
        # debe mirar su variable de entorno DJANGO_SUPERUSER_PASSWORD o regenerarla
        # con `python manage.py reset_admin --username <u> --password <p>`.
        self.stdout.write(self.style.SUCCESS(
            f'➡️  Login del sistema listo para usuario="{username}". '
            f'La contraseña proviene de DJANGO_SUPERUSER_PASSWORD o del fallback interno '
            f'(no se imprime por seguridad).'
        ))