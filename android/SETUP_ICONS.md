# 🎨 Android App Icons Setup

## Current Status

The Android app references launcher icons that need to be created:
- `ic_launcher` (various densities)
- `ic_launcher_round` (various densities)

## Option 1: Use Existing PWA Icons (Quick)

The PWA already has icons in `/static/img/`:
- `icon-192.png` (192x192)
- `icon-512.png` (512x512)

### Steps to Convert:

1. **Download icons from server:**
   ```bash
   # If server is running
   wget https://soptraloc.onrender.com/static/img/icon-192.png
   wget https://soptraloc.onrender.com/static/img/icon-512.png
   ```

2. **Use Android Asset Studio:**
   - Visit: https://romannurik.github.io/AndroidAssetStudio/icons-launcher.html
   - Upload `icon-512.png`
   - Generate all sizes
   - Download zip
   - Extract to `android/app/src/main/res/`

3. **Or use ImageMagick (command line):**
   ```bash
   cd /path/to/soptraloc
   
   # Copy source icon
   SOURCE_ICON="static/img/icon-512.png"
   
   # Create directories
   mkdir -p android/app/src/main/res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}
   
   # Generate icons for each density
   convert $SOURCE_ICON -resize 48x48 android/app/src/main/res/mipmap-mdpi/ic_launcher.png
   convert $SOURCE_ICON -resize 72x72 android/app/src/main/res/mipmap-hdpi/ic_launcher.png
   convert $SOURCE_ICON -resize 96x96 android/app/src/main/res/mipmap-xhdpi/ic_launcher.png
   convert $SOURCE_ICON -resize 144x144 android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png
   convert $SOURCE_ICON -resize 192x192 android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
   
   # Generate round icons (same sizes)
   convert $SOURCE_ICON -resize 48x48 android/app/src/main/res/mipmap-mdpi/ic_launcher_round.png
   convert $SOURCE_ICON -resize 72x72 android/app/src/main/res/mipmap-hdpi/ic_launcher_round.png
   convert $SOURCE_ICON -resize 96x96 android/app/src/main/res/mipmap-xhdpi/ic_launcher_round.png
   convert $SOURCE_ICON -resize 144x144 android/app/src/main/res/mipmap-xxhdpi/ic_launcher_round.png
   convert $SOURCE_ICON -resize 192x192 android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_round.png
   ```

## Option 2: Create Custom Android Icons

If you want to create professional Android icons with adaptive icon support:

### 1. Create Vector Drawable (Recommended)

```xml
<!-- android/app/src/main/res/drawable/ic_launcher_foreground.xml -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <!-- Your icon paths here -->
</vector>
```

### 2. Use Android Studio

1. Right-click `res` folder
2. New → Image Asset
3. Choose:
   - Asset Type: Launcher Icons (Adaptive and Legacy)
   - Path: Select your source image
4. Next → Finish
5. Android Studio generates all required sizes

### 3. Use Online Tools

**Tool 1: Android Asset Studio**
- URL: https://romannurik.github.io/AndroidAssetStudio/icons-launcher.html
- Upload 512x512 PNG
- Customize colors, shape
- Download zip with all densities

**Tool 2: App Icon Generator**
- URL: https://appicon.co/
- Upload 1024x1024 image
- Select Android
- Download icons

## Option 3: Use Default Icons (Temporary)

For testing, you can use a simple placeholder:

```bash
cd android/app/src/main/res

# Create simple colored squares using ImageMagick
convert -size 48x48 xc:#667eea mipmap-mdpi/ic_launcher.png
convert -size 72x72 xc:#667eea mipmap-hdpi/ic_launcher.png
convert -size 96x96 xc:#667eea mipmap-xhdpi/ic_launcher.png
convert -size 144x144 xc:#667eea mipmap-xxhdpi/ic_launcher.png
convert -size 192x192 xc:#667eea mipmap-xxxhdpi/ic_launcher.png

# Copy for round icons
for dir in mipmap-*; do
    cp $dir/ic_launcher.png $dir/ic_launcher_round.png
done
```

## Required Icon Sizes

| Density | Size (px) | Directory |
|---------|-----------|-----------|
| mdpi | 48×48 | mipmap-mdpi |
| hdpi | 72×72 | mipmap-hdpi |
| xhdpi | 96×96 | mipmap-xhdpi |
| xxhdpi | 144×144 | mipmap-xxhdpi |
| xxxhdpi | 192×192 | mipmap-xxxhdpi |

## Icon Design Guidelines

**Android Adaptive Icons (API 26+):**
- Foreground: 108×108 dp (safe zone: 66×66 dp in center)
- Background: 108×108 dp (solid color or drawable)
- Avoid placing important content in corners (gets clipped)

**Legacy Icons:**
- Square or slightly rounded corners
- No shadows (Android adds them)
- High contrast for visibility

**Best Practices:**
- Use simple, recognizable shapes
- Test on different backgrounds (dark/light)
- Ensure icon is visible at small sizes (24×24 dp)

## Verification

After adding icons:

```bash
# Check icons exist
cd android/app/src/main/res
find . -name "ic_launcher*"

# Should output:
# ./mipmap-mdpi/ic_launcher.png
# ./mipmap-mdpi/ic_launcher_round.png
# ./mipmap-hdpi/ic_launcher.png
# ... etc
```

## If Icons Are Missing

**During build, you'll see:**
```
ERROR: Resource mipmap/ic_launcher not found
```

**Quick fix:**
1. Use Option 1 or 3 above
2. Or comment out icon references in AndroidManifest.xml (not recommended)

## Recommended Solution

**For immediate testing:**
- Use Option 1 with Android Asset Studio (5 minutes)

**For production:**
- Create professional icons with Android Studio (15 minutes)
- Or hire designer for custom icon

---

**Note:** The app will compile without custom icons if you comment out the icon references in AndroidManifest.xml, but it will use a default Android robot icon, which looks unprofessional.
