"""Libera contenedores cuya fecha/hora de liberación ya llegó."""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.containers.models import Container


class Command(BaseCommand):
    help = 'Advance due planned releases from por_arribar to liberado.'

    def handle(self, *args, **options):
        released = 0
        with transaction.atomic():
            due = Container.objects.select_for_update().filter(
                estado='por_arribar', fecha_liberacion__isnull=False,
                fecha_liberacion__lte=timezone.now(),
            )
            for container in due:
                container.cambiar_estado('liberado', 'system_release_scheduler')
                released += 1
        self.stdout.write(self.style.SUCCESS(f'Liberaciones aplicadas: {released}'))
