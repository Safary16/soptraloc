from typing import Dict, Iterable

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.containers.models import Container
from apps.containers.services.status_utils import (
    ACTIVE_STATUS_CODES,
    normalize_status,
    related_status_values,
)


class Command(BaseCommand):
    help = "Normaliza los estados de contenedores y detecta posibles duplicados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los cambios que se aplicarían sin modificarlos en la base de datos.",
        )
        parser.add_argument(
            "--only-report",
            action="store_true",
            help="Solo genera los reportes de estado y duplicados sin intentar normalizar.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_report = options["only_report"]

        self.stdout.write(self.style.MIGRATE_HEADING("🔎 Diagnóstico de contenedores"))

        duplicates = self._find_duplicates()
        if duplicates:
            self.stdout.write(self.style.WARNING("⚠️ Se encontraron contenedores duplicados por número:"))
            for container_number, total in duplicates:
                self.stdout.write(f"  • {container_number}: {total} registros")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No se detectaron números de contenedor duplicados"))

        status_report = self._status_breakdown()
        self.stdout.write("\n📊 Distribución de estados (antes de normalizar):")
        for code, count in sorted(status_report.items()):
            normalized = normalize_status(code)
            suffix = "" if normalized == code else f" → {normalized}"
            self.stdout.write(f"  • {code or '∅'}{suffix}: {count}")

        if only_report:
            return

        updated = self._normalize_statuses(dry_run=dry_run)
        if dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    f"🔁 Modo simulación: {updated} contenedores requerirían actualización de estado"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Estados normalizados correctamente ({updated} registros actualizados)")
            )

        normalized_report = self._status_breakdown()
        self.stdout.write("\n📊 Distribución de estados (tras normalizar):")
        for code, count in sorted(normalized_report.items()):
            self.stdout.write(f"  • {code}: {count}")

        active_total = sum(
            normalized_report.get(code, 0) for code in ACTIVE_STATUS_CODES
        )
        self.stdout.write(
            f"\n🚚 Contenedores operativos visibles en dashboard: {active_total}"
        )

    def _find_duplicates(self) -> Iterable[tuple[str, int]]:
        return list(
            Container.objects.values("container_number")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .values_list("container_number", "total")
        )

    def _status_breakdown(self) -> Dict[str, int]:
        return dict(
            Container.objects.values("status")
            .annotate(total=Count("id"))
            .order_by("status")
            .values_list("status", "total")
        )

    def _normalize_statuses(self, dry_run: bool) -> int:
        updated = 0
        with transaction.atomic():
            for container in Container.objects.all().only("id", "status"):
                normalized = normalize_status(container.status)
                if normalized != container.status:
                    updated += 1
                    if not dry_run:
                        container.status = normalized
                        container.save(update_fields=["status"])
            if dry_run:
                transaction.set_rollback(True)
        return updated
