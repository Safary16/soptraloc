import random
import string
from django.contrib.auth.models import User
from django.utils.text import slugify

def generar_password_temporal(length=12):
    """Genera una contraseña aleatoria segura."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

def asegurar_acceso(driver):
    """
    Crea o resetea el User de Django vinculado a un Driver.
    Cada llamada genera una nueva contraseña temporal (comportamiento de
    "regenerar acceso"): la anterior deja de ser válida.
    Retorna dict con 'username' y 'temporary_password'.
    """
    username = slugify(driver.nombre.lower().replace(" ", "."))
    
    # Asegurar unicidad de username
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exclude(id=driver.user_id if driver.user else None).exists():
        username = f"{base_username}.{counter}"
        counter += 1

    temp_password = generar_password_temporal()
    if not driver.user:
        user = User.objects.create_user(
            username=username,
            password=temp_password,
            first_name=driver.nombre[:30]
        )
        driver.user = user
        driver.save()
    else:
        user = driver.user
        changed = []
        if user.username != username:
            user.username = username
            changed.append('username')
        user.set_password(temp_password)
        changed.append('password')
        user.save(update_fields=changed)

    return {
        'username': user.username,
        'temporary_password': temp_password,
    }


# Alias de compatibilidad (nombre histórico usado por algunos módulos)
asegurar_acceso_conductor = asegurar_acceso
