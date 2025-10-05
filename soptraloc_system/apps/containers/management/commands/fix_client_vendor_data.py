"""
Django management command para corregir datos de clientes en contenedores.

Uso:
    python manage.py fix_client_vendor_data
    python manage.py fix_client_vendor_data --dry-run  # Ver sin modificar
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.containers.models import Container
from apps.containers.services.excel_importers import _get_or_create_company

User = get_user_model()


class Command(BaseCommand):
    help = 'Corrige datos de clientes en contenedores (vendor → Cliente Demo)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se haría sin modificar la BD',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.MIGRATE_HEADING(
            "CORRECCIÓN DE DATOS: Cliente vs Vendor"
        ))
        self.stdout.write("="*70 + "\n")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "⚠️  MODO DRY-RUN: No se modificará la base de datos\n"
            ))
        
        # Obtener todos los contenedores
        containers = Container.objects.select_related('client', 'owner_company').all()
        total = containers.count()
        
        self.stdout.write(f"📊 Total de contenedores en BD: {total}\n")
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                "✅ No hay contenedores para procesar."
            ))
            return
        
        # Mostrar estado actual (primeros 5)
        self.stdout.write("📋 ESTADO ACTUAL (primeros 5):")
        self.stdout.write("-" * 70)
        for container in containers[:5]:
            client_name = container.client.name if container.client else "NULL"
            owner_name = container.owner_company.name if container.owner_company else "NULL"
            self.stdout.write(
                f"  {container.container_number:15} | "
                f"Cliente: {client_name:30} | "
                f"Owner: {owner_name}"
            )
        
        # Identificar contenedores con problema
        problematic = []
        for container in containers:
            # Si el cliente NO es "Cliente Demo", hay problema
            if not container.client or container.client.name != "Cliente Demo":
                problematic.append(container)
        
        self.stdout.write(f"\n⚠️  Contenedores con problema: {len(problematic)}\n")
        
        if len(problematic) == 0:
            self.stdout.write(self.style.SUCCESS(
                "✅ Todos los contenedores tienen 'Cliente Demo' correctamente."
            ))
            return
        
        if dry_run:
            self.stdout.write("\n🔍 CONTENEDORES QUE SE ACTUALIZARÍAN:")
            self.stdout.write("-" * 70)
            for i, container in enumerate(problematic[:10], 1):
                old_client = container.client.name if container.client else "NULL"
                self.stdout.write(
                    f"  {i:2}. {container.container_number:15} | "
                    f"{old_client:30} → Cliente Demo"
                )
            if len(problematic) > 10:
                self.stdout.write(f"  ... y {len(problematic) - 10} más")
            
            self.stdout.write(f"\n💡 Ejecuta sin --dry-run para aplicar cambios\n")
            return
        
        # APLICAR CAMBIOS
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR(
                "❌ ERROR: No hay usuarios en el sistema. No se puede crear 'Cliente Demo'."
            ))
            return
        
        self.stdout.write(f"🔧 Usando usuario: {user.email}\n")
        
        # Crear o obtener "Cliente Demo"
        client_demo = _get_or_create_company("Cliente Demo", user)
        self.stdout.write(self.style.SUCCESS(
            f"✅ Cliente Demo: {client_demo.name} (ID: {client_demo.id})\n"
        ))
        
        # Actualizar contenedores
        self.stdout.write(f"🔄 Actualizando {len(problematic)} contenedores...")
        self.stdout.write("-" * 70)
        
        updated_count = 0
        for container in problematic:
            old_client = container.client.name if container.client else "NULL"
            container.client = client_demo
            container.save()
            updated_count += 1
            
            if updated_count <= 10:  # Mostrar primeros 10
                self.stdout.write(
                    f"  ✓ {container.container_number:15} | "
                    f"{old_client:30} → Cliente Demo"
                )
        
        if updated_count > 10:
            self.stdout.write(f"  ... y {updated_count - 10} más")
        
        # Verificar resultado
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.MIGRATE_HEADING("VERIFICACIÓN FINAL"))
        self.stdout.write("="*70 + "\n")
        
        containers_updated = Container.objects.select_related('client', 'owner_company').all()
        
        self.stdout.write("📋 ESTADO FINAL (primeros 5):")
        self.stdout.write("-" * 70)
        for container in containers_updated[:5]:
            client_name = container.client.name if container.client else "NULL"
            owner_name = container.owner_company.name if container.owner_company else "NULL"
            status_icon = "✅" if client_name == "Cliente Demo" else "❌"
            self.stdout.write(
                f"  {status_icon} {container.container_number:15} | "
                f"Cliente: {client_name:30} | "
                f"Owner: {owner_name}"
            )
        
        # Contar por estado
        demo_count = Container.objects.filter(client__name="Cliente Demo").count()
        other_count = total - demo_count
        
        self.stdout.write(f"\n📊 RESUMEN:")
        self.stdout.write(f"  ✅ Cliente Demo: {demo_count}")
        self.stdout.write(f"  ❌ Otros clientes: {other_count}")
        self.stdout.write(f"  📦 Total: {total}")
        
        if other_count == 0:
            self.stdout.write(self.style.SUCCESS(
                "\n🎉 ¡ÉXITO! Todos los contenedores tienen 'Cliente Demo'"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  ADVERTENCIA: {other_count} contenedores aún no tienen 'Cliente Demo'"
            ))
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS(
            f"✅ Proceso completado: {updated_count} contenedores actualizados"
        ))
        self.stdout.write("="*70 + "\n")
