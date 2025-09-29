# 🖥️ GUÍA COMPLETA DE ACCESO Y GESTIÓN DE ARCHIVOS - SOPTRALOC

## 📍 UBICACIÓN ACTUAL
- **Sistema**: GitHub Codespaces (Linux Ubuntu)
- **Usuario**: codespace 
- **Proyecto**: `/workspaces/soptraloc/`
- **IP**: 10.0.10.130 (interna)

---

## 🎯 MÉTODOS DE ACCESO

### 1. **VS Code (ACTUAL - RECOMENDADO)**
✅ **Ya lo estás usando**
- Navegador de archivos: Panel izquierdo
- Terminal integrado: `Ctrl + `` 
- Editor completo con IntelliSense
- Git integrado
- Extensiones Python/Django

### 2. **Terminal Directo**
```bash
# Navegar al proyecto
cd /workspaces/soptraloc/soptraloc_system

# Editar archivos
nano apps/containers/models.py
vim config/settings.py  
code apps/core/views.py
```

### 3. **Comandos de Gestión Rápida**
```bash
# Ver estructura
tree -L 2 /workspaces/soptraloc/

# Buscar archivos
find . -name "*.py" | head -10
find . -name "models.py"
find . -name "*views*"

# Editar archivos importantes
code config/settings.py        # Configuración Django
code apps/containers/models.py # Modelos de containers
code config/urls.py           # URLs del proyecto
```

---

## 📁 ESTRUCTURA DE ARCHIVOS IMPORTANTES

```
soptraloc_system/
├── 🔧 config/
│   ├── settings.py    # Configuración Django
│   ├── urls.py        # URLs principales
│   └── wsgi.py        # Servidor web
├── 📦 apps/
│   ├── containers/    # Sistema de contenedores
│   ├── core/          # Funciones core
│   ├── warehouses/    # Almacenes
│   └── scheduling/    # Programación
├── 🌐 templates/      # Plantillas HTML
├── 📊 static/         # Archivos CSS/JS
└── 🗃️ db.sqlite3      # Base de datos
```

---

## 🔧 COMANDOS ESENCIALES

### **Edición de Archivos:**
```bash
# Método 1: VS Code (recomendado)
code archivo.py

# Método 2: Editor simple
nano archivo.py

# Método 3: Editor avanzado
vim archivo.py
```

### **Navegación:**
```bash
ls -la                    # Listar archivos
cd apps/containers        # Entrar a carpeta
pwd                       # Ver ubicación actual
tree                      # Ver estructura (si está disponible)
```

### **Búsqueda:**
```bash
grep -r "class Container" .    # Buscar texto en archivos
find . -name "*.py"           # Buscar archivos Python
locate settings.py            # Localizar archivo
```

### **Django Específico:**
```bash
python manage.py shell        # Console Django
python manage.py runserver    # Iniciar servidor
python manage.py migrate      # Aplicar migraciones
python manage.py collectstatic # Archivos estáticos
```

---

## 💾 SUBIR/MODIFICAR ARCHIVOS

### **Opción 1: VS Code Interface**
1. Panel izquierdo → Explorador
2. Clic derecho → "New File" / "New Folder"  
3. Arrastrar y soltar archivos
4. Editar directamente en el editor

### **Opción 2: Terminal**
```bash
# Crear archivo
touch nuevo_archivo.py
echo "print('Hola')" > test.py

# Copiar archivo
cp origen.py destino.py

# Mover/renombrar
mv archivo_viejo.py archivo_nuevo.py

# Crear carpeta
mkdir nueva_carpeta
```

### **Opción 3: Comandos Git**
```bash
git add .                # Añadir cambios
git commit -m "mensaje"  # Confirmar cambios
git push                 # Subir a repositorio
```

---

## 🌐 ACCESO EXTERNO (Si necesitas)

### **URLs de Acceso:**
- **Aplicación**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/v1/
- **Swagger**: http://localhost:8000/swagger/

### **Puertos Abiertos:**
- 8000: Servidor Django
- 22: SSH (si está habilitado)

---

## 🔑 PERMISOS Y SEGURIDAD

```bash
# Ver permisos actuales
ls -la archivo.py

# Cambiar permisos
chmod 755 script.sh     # Ejecutable
chmod 644 archivo.py    # Solo lectura/escritura

# Ver usuario actual
whoami                  # codespace
id                      # Información completa
```

---

## ⚡ ATAJOS ÚTILES EN VS CODE

| Atajo | Función |
|-------|---------|
| `Ctrl + `` | Abrir/cerrar terminal |
| `Ctrl + P` | Buscar archivos |
| `Ctrl + Shift + P` | Paleta de comandos |
| `Ctrl + S` | Guardar archivo |
| `Ctrl + F` | Buscar en archivo |
| `Ctrl + H` | Buscar y reemplazar |

---

## 🚨 ESTADO ACTUAL DEL SERVIDOR

✅ **Servidor Django**: EJECUTÁNDOSE  
🌐 **URL**: http://localhost:8000  
📁 **Base de datos**: SQLite (`db.sqlite3`)  
🔧 **Modo**: DEBUG=True (desarrollo)  

---

## 💡 RECOMENDACIÓN

**Para tu caso, usa VS Code** que ya tienes abierto:
1. Panel izquierdo para navegar archivos
2. Editor central para modificar código  
3. Terminal integrado para comandos
4. Git integrado para versionado

¡Es la forma más eficiente y completa de trabajar con tu proyecto SoptraLoc!