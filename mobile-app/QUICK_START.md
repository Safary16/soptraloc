# 🚀 Quick Start - SoptraLoc Native App

## ⚡ 5-Minute Setup

### Step 1: Prerequisites (if not installed)
```bash
# Check Node.js
node --version  # Need 16+

# If not installed:
# Ubuntu/Debian: sudo apt install nodejs npm
# macOS: brew install node
# Windows: Download from nodejs.org
```

### Step 2: Install Dependencies
```bash
cd mobile-app/
npm install
```

Expected output:
```
✔ Dependencies installed successfully
```

Time: 2-3 minutes

### Step 3: Build Debug APK
```bash
npm run build:android-debug
```

Expected output:
```
BUILD SUCCESSFUL
```

APK location: `android/app/build/outputs/apk/debug/app-debug.apk`

Time: 3-5 minutes (first time)

### Step 4: Install on Device
```bash
# Connect Android phone via USB
# Enable Developer Options + USB Debugging

adb install android/app/build/outputs/apk/debug/app-debug.apk
```

Expected output:
```
Success
```

---

## 📱 First Use

1. **Open app** "SoptraLoc Driver"
2. **Enter patente** (e.g., "ABCD12")
3. **Tap** "Iniciar Sesión"
4. **Allow permissions** "Permitir siempre"
5. **Tap** "Iniciar Tracking"
6. **Lock phone** 🔒
7. **Wait 2 minutes**
8. **Unlock and verify** "Última ubicación" updated

---

## 🧪 Verify It Works

### On Phone:
- Notification shows "SoptraLoc - Tracking Activo" ✅
- Last location timestamp updates every 30s ✅

### On Computer:
1. Open `https://soptraloc.onrender.com/monitoring/`
2. See driver's location on map ✅
3. Location updates every 30s ✅

**If both work → SUCCESS! GPS works with screen locked!**

---

## 🆘 Troubleshooting

### Problem: "Build failed"
```bash
cd android/
./gradlew clean
cd ..
npm run build:android-debug
```

### Problem: "adb not found"
```bash
# Install Android SDK
# Set ANDROID_HOME environment variable
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

### Problem: "GPS not working when locked"
```
Settings → Apps → SoptraLoc Driver → Permissions
→ Location → Select "Allow all the time" (not "While using")
```

---

## 📖 More Information

- **Full guide:** `/NATIVE_APP_GUIDE.md`
- **Build details:** `BUILD_INSTRUCTIONS.md`
- **Why native:** `/MIGRATION_PWA_TO_NATIVE.md`

---

## ✅ Success Criteria

- [ ] APK compiled without errors
- [ ] App installs on device
- [ ] Login with patente works
- [ ] GPS tracking starts
- [ ] Notification shows
- [ ] Can lock phone
- [ ] Location updates continue
- [ ] Backend receives data
- [ ] Monitoring shows location

**All checked? Congratulations! Ready for pilot deployment!**
