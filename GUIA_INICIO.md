# SoptraLoc — inicio rápido

## 1. Crear el acceso administrador en Render

Al crear el servicio desde `render.yaml`, Render solicitará dos secretos:

- `DJANGO_SUPERUSER_EMAIL`: tu correo (recomendado, aunque puede quedar vacío).
- `DJANGO_SUPERUSER_PASSWORD`: una clave nueva de al menos 12 caracteres.

El usuario queda fijado como `admin`. La clave **no viene escrita en el repositorio**: es la que tú ingreses en Render.

Después del primer despliegue:

1. Abre `https://TU-SERVICIO.onrender.com/admin/`.
2. Usuario: `admin`.
3. Contraseña: la que guardaste en `DJANGO_SUPERUSER_PASSWORD`.

Si olvidaste la clave, abre el servicio en Render → **Environment**, cambia
`DJANGO_SUPERUSER_PASSWORD` y vuelve a desplegar. `start.sh` actualiza el acceso
de forma segura al arrancar.

## 2. Agregar un CD

1. Inicia sesión como administrador.
2. En el menú abre **Datos maestros → Centros de distribución**.
3. Pulsa **Nuevo CD**.
4. Completa nombre, dirección, comuna, tipo, latitud y longitud.
5. El radio de geocerca es opcional. Si queda vacío, el arribo automático queda inactivo.
6. Guarda.

## 3. Agregar un contenedor

1. Abre **Contenedores**.
2. Pulsa **Nuevo contenedor**.
3. Ingresa un ID con 4 letras y 7 números, por ejemplo `MSCU1234567`.
4. Completa nave y tipo. Los demás campos pueden agregarse ahora o editarse después.
5. Si el CD todavía no existe, créalo primero desde **Datos maestros**.
6. Guarda.

Para muchos contenedores, usa **Importar** y carga el Excel de embarque.

## 4. Agregar un conductor

1. Abre **Datos maestros → Conductores**.
2. Pulsa **Nuevo conductor**.
3. Al guardar se muestra una contraseña temporal una sola vez.
4. Copia usuario y clave y entrégalos al conductor.
5. Si se pierde, usa el botón de llave para regenerarla.

Los botones de desactivar/cancelar conservan el historial; no borran los datos operacionales.
