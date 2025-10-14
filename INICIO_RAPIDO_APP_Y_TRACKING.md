# ⚡ Inicio Rápido: App Nativa + Tracking Histórico

## 📱 Para Conductores: Instalar App Móvil

### Android/Chrome (30 segundos)
1. Abrir Chrome
2. Ir a: `https://soptraloc.onrender.com/driver/login/`
3. Hacer login
4. Aparece banner morado → Click "Instalar Ahora"
5. ✅ ¡Listo! App instalada

### iOS/Safari (30 segundos)
1. Abrir Safari
2. Ir a: `https://soptraloc.onrender.com/driver/login/`
3. Hacer login
4. Botón "Compartir" → "Agregar a pantalla de inicio"
5. ✅ ¡Listo! App instalada

**Ventajas:**
- Acceso instantáneo desde icono
- GPS en segundo plano
- Notificaciones de entregas
- Funciona sin internet

---

## 🗺️ Para Admins: Ver Recorrido Histórico

### Caso 1: Ver ruta de ayer (10 segundos)
1. Ir a: `https://soptraloc.onrender.com/monitoring/`
2. En "Seguimiento Histórico":
   - Conductor: Seleccionar nombre
   - Período: "Últimas 24 horas"
3. Click "Ver Recorrido"
4. ✅ Mapa muestra ruta completa

### Caso 2: Ver ruta de fecha específica (20 segundos)
1. Ir a: `https://soptraloc.onrender.com/monitoring/`
2. En "Seguimiento Histórico":
   - Conductor: Seleccionar nombre
   - Período: "Personalizado"
   - Desde: `2025-10-10 08:00`
   - Hasta: `2025-10-10 18:00`
3. Click "Ver Recorrido"
4. ✅ Mapa muestra ruta del día seleccionado

**En el mapa verás:**
- 🟢 Bandera verde = inicio de ruta
- 🏁 Bandera a cuadros = fin de ruta  
- Línea roja = recorrido completo
- Puntos rojos = ubicaciones intermedias (click para ver hora)

---

## 🎯 URLs Importantes

| Página | URL |
|--------|-----|
| Login Conductor | `/driver/login/` |
| Dashboard (instalar app) | `/driver/dashboard/` |
| Monitoreo + Tracking | `/monitoring/` |
| Admin | `/admin/` |

---

## 💡 Casos de Uso Rápidos

### ✅ Cliente dice "nunca llegó el conductor"
**Solución (30 segundos):**
1. `/monitoring/` → Seguimiento Histórico
2. Seleccionar conductor y fecha del reclamo
3. "Ver Recorrido"
4. Mostrar evidencia GPS al cliente

### ✅ Verificar entregas del día
**Solución (10 segundos):**
1. `/monitoring/` → Seguimiento Histórico
2. Seleccionar conductor
3. Período: "Últimas 24 horas"
4. "Ver Recorrido"
5. Revisar puntos visitados

### ✅ Auditar ruta de la semana
**Solución (15 segundos):**
1. `/monitoring/` → Seguimiento Histórico
2. Seleccionar conductor
3. Período: "Última semana"
4. "Ver Recorrido"
5. Analizar eficiencia de rutas

---

## 🆘 Problemas Comunes

### App no se instala
- ✅ Usar Chrome (Android) o Safari (iOS)
- ✅ Actualizar navegador a última versión
- ✅ Verificar internet estable

### GPS no se actualiza
- ✅ Verificar permisos de ubicación en teléfono
- ✅ Reiniciar app
- ✅ Activar servicio de ubicación

### Historial no carga
- ✅ Verificar que haya datos en el período
- ✅ Probar con período más amplio
- ✅ Refrescar página (F5)

---

## 📞 Soporte

**Documentación completa:**
- `GUIA_APP_NATIVA_Y_TRACKING_HISTORICO.md`
- `RESUMEN_APP_NATIVA_Y_TRACKING.md`

**Ayuda técnica:**
- Admin panel: `/admin/`
- Ver logs del sistema

---

## 🚀 Próximos Pasos

1. **Probar instalación** - Un conductor instala la app
2. **Probar tracking** - Ver su recorrido de hoy
3. **Capacitar equipo** - Mostrar funcionalidades
4. **Comunicar a conductores** - Email con link de instalación

---

**Última actualización:** 2025-10-14  
**Versión:** 1.0.0
