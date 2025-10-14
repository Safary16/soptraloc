# PWA Icons Required

Para que la PWA funcione correctamente, se necesitan los siguientes iconos:

## Iconos Requeridos:

1. **icon-192.png** (192x192 pixels)
   - Usado para pantalla de inicio en Android
   - Icono principal de la app

2. **icon-512.png** (512x512 pixels)  
   - Usado para splash screen
   - Alta resolución para dispositivos grandes

3. **badge.png** (96x96 pixels) - Opcional
   - Usado en notificaciones como badge
   - Versión simplificada del logo

## Cómo Crear los Iconos:

### Opción 1: Usar Logo Existente
Si tienen un logo de SoptraLoc:
1. Abrir en editor de imágenes (Photoshop, GIMP, Figma)
2. Exportar en 192x192 y 512x512 con fondo sólido
3. Guardar como PNG

### Opción 2: Crear Icono Simple
Usar un generador online:
- https://realfavicongenerator.net/
- https://www.favicon-generator.org/
- https://favicon.io/

### Opción 3: Placeholder Temporal
Para testing, usar un ícono genérico:
```bash
# Crear ícono placeholder con ImageMagick
convert -size 192x192 xc:#667eea -gravity center \
  -pointsize 100 -fill white -annotate +0+0 "S" \
  icon-192.png

convert -size 512x512 xc:#667eea -gravity center \
  -pointsize 300 -fill white -annotate +0+0 "S" \
  icon-512.png
```

## Ubicación:
```
static/img/
├── icon-192.png
├── icon-512.png
└── badge.png (opcional)
```

## Verificación:
Una vez creados los iconos, verificar en:
- Chrome DevTools → Application → Manifest
- Debe mostrar los iconos correctamente
