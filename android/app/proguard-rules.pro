# Add project specific ProGuard rules here.
# Mantener clases de androidbrowserhelper
-keep class com.google.androidbrowserhelper.** { *; }
-dontwarn com.google.androidbrowserhelper.**

# Mantener servicios de ubicación
-keep class * extends android.app.Service
-keepclassmembers class * extends android.app.Service {
    public <init>(...);
}
