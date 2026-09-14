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
    # Nota: exclude(id=...) con None no filtra en Django; se usa consulta
    # sin exclusión cuando el driver aún no tiene user asociado.
    if driver.user_id:
        existe_username = User.objects.filter(username=username).exclude(id=driver.user_id).exists
    else:
        existe_username = User.objects.filter(username=username).exists
    while existe_username():
        username = f"{base_username}.{counter}"
        counter += 1
        if driver.user_id:
            existe_username = User.objects.filter(username=username).exclude(id=driver.user_id).exists
        else:
            existe_username = User.objects.filter(username=username).exists

    temp_password = generar_password_temporal()
    if not driver.user:
        names = driver.nombre.split()
        first_name = names[0][:30] if names else ''
        last_name = ' '.join(names[1:])[:30] if len(names) > 1 else ''
        user = User.objects.create_user(
            username=username,
            password=temp_password,
            first_name=first_name,
            last_name=last_name,
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
