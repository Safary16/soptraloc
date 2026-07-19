"""Provisionamiento seguro de acceso para conductores."""
import secrets
import string
import unicodedata

from django.contrib.auth.models import User
from django.db import transaction


def generar_username(nombre):
    normalized = unicodedata.normalize('NFD', nombre or '')
    ascii_name = normalized.encode('ascii', 'ignore').decode('utf-8')
    base = ''.join(c for c in ascii_name.lower().replace(' ', '_') if c.isalnum() or c == '_')
    base = base.strip('_') or 'conductor'
    username, counter = base, 1
    while User.objects.filter(username=username).exists():
        username = f'{base}_{counter}'
        counter += 1
    return username


def generar_password_temporal(length=14):
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password) and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
            return password


@transaction.atomic
def asegurar_acceso(driver, *, username=None, password=None):
    """Crea o restablece acceso y devuelve la clave solo en esta llamada."""
    temporary_password = password or generar_password_temporal()
    if driver.user_id:
        user = User.objects.select_for_update().get(pk=driver.user_id)
        if username and username != user.username:
            if User.objects.exclude(pk=user.pk).filter(username=username).exists():
                raise ValueError('El nombre de usuario ya existe.')
            user.username = username
    else:
        requested = (username or '').strip()
        if requested and User.objects.filter(username=requested).exists():
            raise ValueError('El nombre de usuario ya existe.')
        user = User(username=requested or generar_username(driver.nombre))
    names = (driver.nombre or '').split()
    user.first_name = names[0] if names else ''
    user.last_name = ' '.join(names[1:])
    user.is_active = driver.activo
    user.set_password(temporary_password)
    user.save()
    if driver.user_id != user.id:
        driver.user = user
        driver.save(update_fields=['user', 'updated_at'])
    return {'username': user.username, 'temporary_password': temporary_password}
