# 🔨 Build Instructions - SoptraLoc Native App

## 📋 Prerequisites

### Required Software:

1. **Node.js 16+**
   ```bash
   # Check version
   node --version  # Should be v16.x or higher
   npm --version   # Should be 8.x or higher
   ```

2. **Java Development Kit (JDK) 11**
   ```bash
   # Check version
   java -version   # Should be 11.x
   javac -version
   
   # Ubuntu/Debian
   sudo apt install openjdk-11-jdk
   
   # macOS
   brew install openjdk@11
   ```

3. **Android SDK**
   
   **Option A: Android Studio (Recommended)**
   - Download from: https://developer.android.com/studio
   - Install with default settings
   - SDK will be in: `~/Android/Sdk` (Linux/Mac) or `C:\Users\<user>\AppData\Local\Android\Sdk` (Windows)
   
   **Option B: Command Line Tools Only**
   ```bash
   # Download from: https://developer.android.com/studio#command-tools
   # Extract to: ~/Android/cmdline-tools
   ```

4. **Environment Variables**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export ANDROID_HOME=$HOME/Android/Sdk
   export PATH=$PATH:$ANDROID_HOME/emulator
   export PATH=$PATH:$ANDROID_HOME/tools
   export PATH=$PATH:$ANDROID_HOME/tools/bin
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   
   # Reload shell
   source ~/.bashrc  # or source ~/.zshrc
   ```

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd mobile-app/
npm install
```

This will install all required packages including:
- React Native 0.72.6
- react-native-geolocation-service
- react-native-background-actions
- @react-native-async-storage/async-storage
- axios

**Expected output:**
```
added 1234 packages in 2m
```

### Step 2: Verify Android SDK

```bash
# Check Android SDK is accessible
$ANDROID_HOME/platform-tools/adb --version

# Should output something like:
# Android Debug Bridge version 1.0.41
```

If this fails, verify ANDROID_HOME is set correctly.

---

## 📦 Building APK

### Debug APK (for testing)

```bash
cd mobile-app/

# Option 1: Using npm script
npm run build:android-debug

# Option 2: Using Gradle directly
cd android/
./gradlew assembleDebug
cd ..
```

**Output Location:**
```
android/app/build/outputs/apk/debug/app-debug.apk
```

**File Size:** ~30-40 MB

**Time:** 2-5 minutes (first build), 30-60 seconds (subsequent builds)

### Release APK (for production)

#### First Time Setup - Create Keystore

```bash
cd mobile-app/android/app/

# Generate keystore
keytool -genkeypair -v -storetype PKCS12 \
  -keystore soptraloc-release.keystore \
  -alias soptraloc-key \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# You will be prompted for:
# - Keystore password (REMEMBER THIS!)
# - Your name
# - Organization
# - City, State, Country
```

**⚠️ CRITICAL:** Save the keystore file and password securely!
- If lost, you cannot publish app updates
- Store in password manager + backup location

#### Configure Release Signing

```bash
# Create gradle.properties with credentials
cd mobile-app/android/

# Add these lines (replace with your values)
echo "MYAPP_RELEASE_STORE_FILE=app/soptraloc-release.keystore" >> gradle.properties
echo "MYAPP_RELEASE_KEY_ALIAS=soptraloc-key" >> gradle.properties
echo "MYAPP_RELEASE_STORE_PASSWORD=your_keystore_password" >> gradle.properties
echo "MYAPP_RELEASE_KEY_PASSWORD=your_key_password" >> gradle.properties
```

**Security Note:** Do NOT commit `gradle.properties` with real passwords to Git!

#### Build Release APK

```bash
cd mobile-app/

# Using npm script
npm run build:android

# Or using Gradle
cd android/
./gradlew assembleRelease
cd ..
```

**Output Location:**
```
android/app/build/outputs/apk/release/app-release.apk
```

**File Size:** ~25-35 MB (smaller than debug due to ProGuard optimization)

---

## 🧹 Clean Build

If you encounter build errors, try cleaning:

```bash
cd mobile-app/android/

# Clean all build artifacts
./gradlew clean

# Also clean node_modules if needed
cd ..
rm -rf node_modules/
npm install
```

---

## 🔍 Troubleshooting

### Error: "SDK location not found"

**Solution:**
```bash
# Create local.properties manually
cd mobile-app/android/
echo "sdk.dir=$ANDROID_HOME" > local.properties
```

### Error: "JAVA_HOME is not set"

**Solution:**
```bash
# Find Java installation
which java
# Example output: /usr/bin/java

# Set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> ~/.bashrc
```

### Error: "Execution failed for task ':app:mergeDebugResources'"

**Solution:**
```bash
# Missing Android SDK components
$ANDROID_HOME/tools/bin/sdkmanager "platforms;android-33"
$ANDROID_HOME/tools/bin/sdkmanager "build-tools;33.0.0"
```

### Error: "Could not resolve all files for configuration"

**Solution:**
```bash
# Network issue with Maven repositories
# Add to mobile-app/android/build.gradle:

allprojects {
    repositories {
        maven { url 'https://maven.google.com' }
        maven { url 'https://jitpack.io' }
        mavenCentral()
        google()
    }
}
```

### Error: "Duplicate class found"

**Solution:**
```bash
# Clean build and rebuild
cd mobile-app/android/
./gradlew clean
./gradlew assembleDebug --stacktrace
```

---

## 📱 Installing APK on Device

### Method 1: USB Connection (ADB)

```bash
# Enable Developer Options on phone:
# Settings → About Phone → Tap "Build Number" 7 times

# Enable USB Debugging:
# Settings → Developer Options → USB Debugging

# Connect phone via USB
adb devices
# Should show your device ID

# Install APK
cd mobile-app/
adb install android/app/build/outputs/apk/debug/app-debug.apk

# Or to reinstall without losing data
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

### Method 2: File Transfer

```bash
# 1. Copy APK to computer
cd mobile-app/
cp android/app/build/outputs/apk/debug/app-debug.apk ~/Desktop/

# 2. Transfer to phone (USB, email, Google Drive, etc.)

# 3. On phone:
# - Settings → Security → Enable "Install from Unknown Sources"
# - Open APK file with File Manager
# - Tap "Install"
```

### Method 3: QR Code (Web Server)

```bash
# Start simple HTTP server
cd mobile-app/android/app/build/outputs/apk/debug/
python3 -m http.server 8080

# Get your local IP
ip addr show | grep "inet "
# Example: 192.168.1.100

# Create QR code for:
# http://192.168.1.100:8080/app-debug.apk

# Scan QR code with phone → Download → Install
```

---

## 🔐 Signing and Security

### Verify APK Signature

```bash
# Check debug APK
jarsigner -verify -verbose -certs \
  android/app/build/outputs/apk/debug/app-debug.apk

# Check release APK
jarsigner -verify -verbose -certs \
  android/app/build/outputs/apk/release/app-release.apk
```

### APK Information

```bash
# Get APK details
$ANDROID_HOME/build-tools/33.0.0/aapt dump badging \
  android/app/build/outputs/apk/debug/app-debug.apk

# Shows:
# - Package name: com.soptraloc
# - Version code: 1
# - Version name: 1.0.0
# - SDK versions
# - Permissions
```

---

## 📊 Build Variants

### Available Variants:

1. **debug** (Development)
   - No code obfuscation
   - Larger file size
   - Fast build time
   - Debug symbols included

2. **release** (Production)
   - ProGuard optimization
   - Smaller file size
   - Longer build time
   - Code obfuscated

### Build Specific Variant:

```bash
cd mobile-app/android/

# Debug
./gradlew assembleDebug

# Release
./gradlew assembleRelease

# Both
./gradlew assemble
```

---

## 🚢 Distribution Options

### Option 1: Direct APK Distribution

**Pros:**
- ✅ No cost
- ✅ Immediate deployment
- ✅ Full control

**Cons:**
- ⚠️ Users must enable "Unknown Sources"
- ⚠️ Manual updates

**Best for:** Small teams, pilot programs

### Option 2: Google Play Store

**Pros:**
- ✅ Standard installation flow
- ✅ Automatic updates
- ✅ Credibility

**Cons:**
- 💰 $25 USD one-time fee
- ⏱️ 1-3 days review time
- 📋 Must comply with Play policies

**Best for:** Large deployments, public apps

### Option 3: Private App Distribution (Google Play)

**Pros:**
- ✅ Play Store infrastructure
- ✅ Controlled user list
- ✅ Automatic updates

**Cons:**
- 💰 Requires Google Workspace ($6/user/month)
- 📋 Still needs Play Store account

**Best for:** Enterprise deployments

---

## 📈 Optimization Tips

### Reduce APK Size:

```gradle
// android/app/build.gradle

android {
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    
    // Only include necessary ABIs
    splits {
        abi {
            enable true
            reset()
            include 'armeabi-v7a', 'arm64-v8a'
            universalApk false
        }
    }
}
```

### Speed Up Build:

```gradle
// android/gradle.properties

# Use parallel execution
org.gradle.parallel=true

# Configure JVM memory
org.gradle.jvmargs=-Xmx4096m

# Use Gradle cache
android.enableBuildCache=true
```

---

## ✅ Pre-Release Checklist

Before releasing to production:

- [ ] Test on multiple devices (different Android versions)
- [ ] Test GPS with screen locked
- [ ] Test login with valid/invalid patente
- [ ] Test battery consumption (overnight)
- [ ] Verify backend API connectivity
- [ ] Test offline mode
- [ ] Check app permissions
- [ ] Verify notification shows correctly
- [ ] Test update scenario (install over previous version)
- [ ] Review ProGuard rules (no crashes in release)
- [ ] Sign APK with production keystore
- [ ] Document version changes

---

## 📞 Support

For build issues:
1. Check this document's troubleshooting section
2. Review error logs carefully
3. Try clean build: `./gradlew clean`
4. Check Android SDK is properly installed
5. Verify all environment variables are set

For development help:
- React Native Docs: https://reactnative.dev/
- Android Developers: https://developer.android.com/

---

**Last Updated:** 2025-10-14  
**Version:** 1.0.0  
**Tested On:** Ubuntu 20.04, macOS 12+, Windows 10+
