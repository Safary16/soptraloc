# ✅ Lista de Verificación para Despliegue en Render

## 🎯 Objetivo
Desplegar SoptraLoc TMS en Render.com desde cero con admin automático

---

## 📋 Pasos para Desplegar

### Paso 1: Verificación Local ✅
- [x] Repositorio actualizado con últimos cambios
- [x] `render.yaml` configurado correctamente
- [x] `build.sh` actualizado con creación de admin
- [x] Todos los archivos commiteados y pusheados

### Paso 2: Crear Blueprint en Render
1. Ve a: https://dashboard.render.com/
2. Click en **"New +"** en la esquina superior derecha
3. Selecciona **"Blueprint"**
4. Conecta tu repositorio: `Safary16/soptraloc`
5. Render detectará automáticamente `render.yaml`
6. Click en **"Apply"**

### Paso 3: Esperar Deploy
- ⏱️ Tiempo estimado: 5-10 minutos
- 📊 Monitorea en: Dashboard → soptraloc → Logs
- ✅ Verifica que aparezca: "✅ Build completado exitosamente"

### Paso 4: Verificar Servicios Creados
Render creará automáticamente:
- [x] Web Service: `soptraloc`
- [x] PostgreSQL Database: `soptraloc-db`

### Paso 5: Probar el Sitio
Accede a las siguientes URLs:

#### 🌐 URLs del Sitio
- **Home**: https://soptraloc.onrender.com/
- **Admin**: https://soptraloc.onrender.com/admin/
- **API**: https://soptraloc.onrender.com/api/containers/

#### 🔐 Credenciales de Admin
```
URL: https://soptraloc.onrender.com/admin/
Username: admin
Password: 1234
```

---

## 🔍 Verificaciones de Seguridad

Una vez que el sitio esté funcionando:

### ✅ Checklist Post-Deploy
- [ ] El sitio carga correctamente
- [ ] Admin panel es accesible
- [ ] Puedes hacer login con admin/1234
- [ ] API responde correctamente
- [ ] Base de datos está conectada

### 🔐 Seguridad (IMPORTANTE)
- [ ] Cambiar contraseña del admin a una segura
  1. Login en admin panel
  2. Authentication → Users → admin
  3. Change password form
  4. Guardar nueva contraseña

- [ ] Verificar que DEBUG=false en Render
  1. Dashboard → soptraloc → Environment
  2. Verificar: `DEBUG = false`

---

## 🐛 Troubleshooting

### Si el deploy falla:

#### Error: "Build failed"
1. Ve a: Dashboard → soptraloc → Logs
2. Busca el error específico
3. Si es de dependencias: verifica `requirements.txt`
4. Si es de permisos: verifica que `build.sh` sea ejecutable

#### Error: "ModuleNotFoundError: No module named 'app'"
**Esto NO debería ocurrir con el render.yaml actual**

Si ocurre:
1. Verifica que `render.yaml` tenga:
   ```yaml
   startCommand: "gunicorn config.wsgi:application"
   ```
2. Elimina el servicio en Render
3. Vuelve a crear usando Blueprint

#### Error: "Database connection failed"
1. Verifica que `soptraloc-db` esté "Available"
2. Ve a: Dashboard → soptraloc → Environment
3. Verifica que `DATABASE_URL` esté presente

---

## 📞 Comandos Útiles

### Ver estado del deploy:
```bash
# En tu máquina local
git log --oneline -5
git status
```

### Forzar re-deploy:
1. Dashboard → soptraloc
2. Manual Deploy → Deploy latest commit

---

## ✅ Deploy Completado

Si todo está bien, deberías ver:

✅ Servicio en estado "Live" (verde)
✅ Admin accesible en https://soptraloc.onrender.com/admin/
✅ Login con admin/1234 funciona
✅ Base de datos conectada y migraciones aplicadas
✅ Archivos estáticos cargados

---

## 📝 Notas Importantes

1. **Primera carga**: Puede tardar hasta 30 segundos en cargar la primera vez
2. **Free tier**: El servicio se duerme después de 15 minutos de inactividad
3. **Wake-up**: Puede tardar 30-60 segundos en despertar
4. **Admin auto-creado**: El usuario admin se crea automáticamente en cada deploy

---

## 🎉 ¡Listo!

Tu aplicación SoptraLoc TMS está desplegada en:
- **URL Principal**: https://soptraloc.onrender.com
- **Admin Panel**: https://soptraloc.onrender.com/admin/

**Próximos pasos**:
1. Cambiar contraseña del admin
2. Importar datos de producción
3. Configurar monitoreo (opcional)

Para más detalles, consulta: `RENDER_DEPLOYMENT.md`
