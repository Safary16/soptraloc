# 🔐 Solución: Problema de Acceso al Admin

## El Problema
El sistema no permitía acceder al panel de administración de Django.

## La Solución

### ✅ Credenciales por Defecto
Si no puedes acceder al admin, usa estas credenciales:

```
Username: admin
Password: admin123
URL: http://localhost:8000/admin/
```

### ✅ Resetear Contraseña del Admin

Si olvidaste tu contraseña o necesitas resetearla, ejecuta:

```bash
python manage.py reset_admin
```

Esto restablecerá la contraseña a `admin123` para el usuario `admin`.

### Opciones Avanzadas

```bash
# Resetear con usuario personalizado
python manage.py reset_admin --username=miusuario --password=mipassword

# Ejemplo:
python manage.py reset_admin --username=operador --password=ops2024
```

## 🎯 Verificación

Después de resetear la contraseña:

1. Ve a: `http://localhost:8000/admin/`
2. Ingresa:
   - **Usuario:** `admin`
   - **Contraseña:** `admin123`
3. Deberías poder acceder al panel de administración

## 🔒 Seguridad en Producción

⚠️ **IMPORTANTE:** En producción, cambia la contraseña inmediatamente:

1. Ingresa al admin
2. Ve a **Authentication and Authorization** → **Users**
3. Selecciona tu usuario
4. Haz clic en **change password form**
5. Ingresa una contraseña segura
6. Guarda los cambios

## 📝 Notas Adicionales

- El comando `reset_admin` también puede **crear** un nuevo usuario admin si no existe
- El usuario admin tiene todos los permisos (`is_superuser=True`)
- El usuario está marcado como staff (`is_staff=True`) para acceder al admin
- El usuario está activo (`is_active=True`)

## 🛠️ Troubleshooting

### "Unknown command: 'reset_admin'"
Asegúrate de que `apps.core` esté en `INSTALLED_APPS` en `config/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'apps.core',
    # ...
]
```

### "User does not exist"
El comando creará automáticamente el usuario si no existe.

### "Permission denied"
Asegúrate de estar ejecutando el comando desde el directorio raíz del proyecto donde está `manage.py`.
