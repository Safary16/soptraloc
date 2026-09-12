import random
import string
from django.contrib.auth.models import User
from django.utils.text import slugify

def generar_password_temporal(length=12):
    """Genera una contraseña aleatoria segura."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

def asegurar_acceso_conductor(driver):
    """
    Crea o actualiza el User de Django vinculado a un Driver.
    Retorna (user, password_temporal) si se creó/resetó, (user, None) si ya existía.
    """
    username = slugify(driver.nombre.lower().replace(" ", "."))
    
    # Asegurar unicidad de username
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exclude(id=driver.user_id if driver.user else None).exists():
        username = f"{base_username}.{counter}"
        counter += 1

    temp_password = None
    if not driver.user:
        temp_password = generar_password_temporal()
        user = User.objects.create_user(
            username=username,
            password=temp_password,
            first_name=driver.nombre[:30]
        )
        driver.user = user
        driver.save()
    else:
        user = driver.user
        if user.username != username:
            user.username = username
            user.save()
            
    return user, temp_password
