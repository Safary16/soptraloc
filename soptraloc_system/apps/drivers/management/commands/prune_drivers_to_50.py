"""Management command para recortar la tabla de conductores dejando solo un número fijo.

Uso: python manage.py prune_drivers_to_50 [--keep 50] [--dry-run] [--force]
Por defecto conserva los conductores más recientes según ``updated_at``.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.drivers.models import Driver


class Command(BaseCommand):
    help = "Elimina conductores redundantes conservando únicamente los más recientes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            type=int,
            default=50,
            help="Cantidad de conductores a conservar (default: 50)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra un resumen sin eliminar registros",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ejecuta la eliminación sin pedir confirmación interactiva",
        )

    def handle(self, *args, **options):
        keep = max(1, options["keep"])
        dry_run = options["dry_run"]
        force = options["force"]

        total = Driver.objects.count()
        if total <= keep:
            self.stdout.write(self.style.SUCCESS(
                f"✅ La base solo tiene {total} conductores, no es necesario eliminar."
            ))
            return

        self.stdout.write(self.style.WARNING("\n=== PRUNE DRIVERS ==="))
        self.stdout.write(f"📊 Conductores en DB: {total}")
        self.stdout.write(f"✅ Se conservarán: {keep}\n")

        # Seleccionar los conductores a conservar (más recientes según updated_at, fallback created_at)
        cutoff_ids = list(
            Driver.objects.order_by("-updated_at", "-created_at").values_list("id", flat=True)[:keep]
        )

        to_delete_qs = Driver.objects.exclude(id__in=cutoff_ids)
        delete_count = to_delete_qs.count()

        if delete_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay registros extra que eliminar."))
            return

        self.stdout.write(self.style.ERROR(f"🗑️  Conductores a eliminar: {delete_count}"))
        sample = list(to_delete_qs.order_by("created_at")[:5].values("nombre", "rut", "created_at"))
        if sample:
            self.stdout.write("Ejemplos:")
            for row in sample:
                created = timezone.localtime(row["created_at"]).strftime("%Y-%m-%d %H:%M") if row["created_at"] else "N/A"
                self.stdout.write(f"  - {row['nombre'] or 'Sin nombre'} (RUT: {row['rut'] or 's/d'}, creado: {created})")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n✅ DRY RUN: no se eliminaron registros."))
            return

        if not force:
            confirmation = input('\nEscriba "ELIMINAR" para confirmar la limpieza: ')
            if confirmation.strip().upper() != "ELIMINAR":
                self.stdout.write(self.style.ERROR("❌ Operación cancelada por el usuario."))
                return

        with transaction.atomic():
            deleted, _ = to_delete_qs.delete()
            self.stdout.write(self.style.SUCCESS(f"\n✅ Eliminados {deleted} conductores."))

        remaining = Driver.objects.count()
        self.stdout.write(self.style.SUCCESS(f"📉 Conductores restantes: {remaining}"))
