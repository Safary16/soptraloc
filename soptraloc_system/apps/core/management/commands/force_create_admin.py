"""
Management command para crear superusuario de forma forzada
Este comando SIEMPRE crea el usuario admin/1234, eliminando el anterior si existe
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea superusuario admin forzadamente (elimina el anterior si existe)'

    def handle(self, *args, **options):
        USERNAME = 'admin'
        EMAIL = 'admin@soptraloc.com'
        PASSWORD = '1234'
        
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.WARNING("🔧 CREACIÓN FORZADA DE SUPERUSUARIO"))
        self.stdout.write("=" * 70)
        self.stdout.write("")
        
        with transaction.atomic():
            # Paso 1: Eliminar usuario existente
            self.stdout.write("1️⃣  Eliminando usuario 'admin' si existe...")
            deleted_count, _ = User.objects.filter(username=USERNAME).delete()
            
            if deleted_count > 0:
                self.stdout.write(self.style.SUCCESS(f"   ✅ Eliminado {deleted_count} usuario(s)"))
            else:
                self.stdout.write("   ℹ️  No había usuario previo")
            
            self.stdout.write("")
            
            # Paso 2: Crear superusuario
            self.stdout.write("2️⃣  Creando superusuario nuevo...")
            
            try:
                user = User.objects.create_superuser(
                    username=USERNAME,
                    email=EMAIL,
                    password=PASSWORD
                )
                
                self.stdout.write(self.style.SUCCESS("   ✅ SUPERUSUARIO CREADO"))
                self.stdout.write(f"   Username: {user.username}")
                self.stdout.write(f"   Email: {user.email}")
                self.stdout.write(f"   ID: {user.id}")
                self.stdout.write(f"   Superusuario: {user.is_superuser}")
                self.stdout.write(f"   Staff: {user.is_staff}")
                self.stdout.write(f"   Activo: {user.is_active}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ ERROR: {e}"))
                raise
            
            self.stdout.write("")
            
            # Paso 3: Verificar password sin authenticate (django-axes requiere request)
            self.stdout.write("3️⃣  Verificando password...")
            
            password_ok = user.check_password(PASSWORD)
            
            if password_ok:
                self.stdout.write(self.style.SUCCESS("   ✅ PASSWORD VERIFICADO CORRECTAMENTE"))
                self.stdout.write(self.style.WARNING("   ⚠️  Login debe verificarse en /admin (requiere request)"))
            else:
                self.stdout.write(self.style.ERROR("   ❌ PASSWORD INCORRECTO"))
                raise Exception("El password no se guardó correctamente")
            
            self.stdout.write("")
            
            # Paso 4: Resumen
            self.stdout.write("4️⃣  Resumen:")
            self.stdout.write(f"   Total usuarios en DB: {User.objects.count()}")
            
            final_user = User.objects.get(username=USERNAME)
            password_ok = final_user.check_password(PASSWORD)
            
            if password_ok:
                self.stdout.write(self.style.SUCCESS("   ✅ Password verificado"))
            else:
                self.stdout.write(self.style.ERROR("   ❌ Password NO coincide"))
                raise Exception("Password no funciona")
        
        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ SUPERUSUARIO CREADO Y VERIFICADO"))
        self.stdout.write("=" * 70)
        self.stdout.write("")
        self.stdout.write("🔗 Accede a: https://soptraloc.onrender.com/admin/")
        self.stdout.write("🔐 Credenciales:")
        self.stdout.write("   Usuario: admin")
        self.stdout.write("   Password: 1234")
        self.stdout.write("")
