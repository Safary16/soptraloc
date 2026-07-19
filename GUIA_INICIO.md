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

Las liberaciones futuras son revisadas automáticamente cada cinco minutos por
el cron `soptraloc-release-due` del Blueprint. Render cobra los cron jobs; si se
usa un plan sin cron, hay que ejecutar `python manage.py release_due_containers`
desde un programador externo con esa misma frecuencia.

## 4. Agregar un conductor

1. Abre **Datos maestros → Conductores**.
2. Pulsa **Nuevo conductor**.
3. Al guardar se muestra una contraseña temporal una sola vez.
4. Copia usuario y clave y entrégalos al conductor.
5. Si se pierde, usa el botón de llave para regenerarla.

Los botones de desactivar/cancelar conservan el historial; no borran los datos operacionales.

## 5. Drop & hook y vacíos

- **Soltar contenedor** deja al conductor disponible inmediatamente, pero el
  contenedor sigue lleno y queda en estado **Soltado en CD**.
- Cuando el CD termina la descarga, el operador abre **Contenedores** y pulsa el
  botón verde de confirmación.
- Solo entonces pasa a **Vacío** y entra al inventario de vacíos del CD.
- En CDs sin drop & hook, el conductor espera y confirma **Notificar vacío**;
  allí se mide desde el arribo hasta la descarga y recién después queda libre.

## 6. Retorno de vacíos

Desde **Contenedores**, un vacío disponible puede iniciar retorno hacia:

- **Depósito de naviera**: al confirmar llegada, termina como **Devuelto**.
- **CCTI**: se valida capacidad antes de salir; al confirmar llegada, termina
  como **Vacío en CCTI** y aumenta el inventario de ese CCTI.

Al iniciar el retorno, el vacío se descuenta inmediatamente del inventario de
su ubicación de origen. Así, un mismo contenedor nunca queda contado en dos
patios simultáneamente.
