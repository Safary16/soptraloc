# 🌊 Deploy en DigitalOcean con GitHub Student Pack

## 🎓 **Activar tu GitHub Student Pack:**
1. Ve a: https://education.github.com/pack
2. Aplica con tu email estudiantil
3. Busca **"DigitalOcean"** en el pack
4. Reclama tu **$200 de crédito gratis**

## 💧 **Crear tu Droplet:**
1. Ve a: https://cloud.digitalocean.com
2. **Create** → **Droplets**
3. **OS:** Ubuntu 24.04 LTS
4. **Plan:** Basic $4/mês (50 meses gratis con tu crédito!)
5. **Datacenter:** Más cercano a Chile (San Francisco)
6. **Authentication:** SSH Key (recomendado) o Password
7. **Hostname:** safary-server

## 🚀 **Deploy Automático (Opción Fácil):**

### **Paso 1: Conectar por SSH**
```bash
ssh root@TU_IP_PUBLICA
```

### **Paso 2: Ejecutar script automático**
```bash
curl -fsSL https://raw.githubusercontent.com/Safary16/soptraloc/main/digitalocean_deploy.sh | bash
```

## 🌐 **Tu aplicación estará disponible en:**
- **URL:** http://TU_IP_PUBLICA/
- **Dashboard:** http://TU_IP_PUBLICA/dashboard/
- **Admin:** http://TU_IP_PUBLICA/admin/

## 🔐 **Credenciales por defecto:**
- **Usuario:** admin  
- **Contraseña:** admin123

## 📱 **Dominio personalizado (Opcional):**
Si quieres un dominio como `safary.tudominio.com`:
1. Compra dominio en Namecheap (también gratis con Student Pack)
2. Apunta DNS a tu IP de DigitalOcean
3. Configura SSL con Let's Encrypt (gratis)

## 💰 **Costos con Student Pack:**
- **Droplet $4/mes** = 50 meses gratis con $200
- **Backup $0.80/mes** (opcional)
- **SSL:** Gratis con Let's Encrypt
- **Dominio:** Gratis con Student Pack (Namecheap)

## ⚡ **Ventajas de DigitalOcean:**
- ✅ **Control total** del servidor
- ✅ **SSH access** completo
- ✅ **Múltiples aplicaciones** en el mismo servidor
- ✅ **Base de datos** incluida
- ✅ **Backups automáticos** opcionales
- ✅ **Escalamiento** manual o automático
- ✅ **50 meses gratis** con Student Pack

¿Quieres que creemos el droplet juntos o prefieres hacerlo tú?