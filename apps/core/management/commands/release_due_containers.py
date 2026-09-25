"""Libera contenedores cuya fecha/hora de liberación ya llegó."""
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.containers.models import Container

logger = logging.getLogger(__name__)


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
                # Preservamos la fecha_liberacion original de la planilla antes
                # de la transición FSM: cambiar_estado() setea el timestamp del
                # nuevo estado a timezone.now(), lo que pisaría la fecha real
                # de liberación que el operador ya ingresó.
                original_fecha_liberacion = container.fecha_liberacion
                container.cambiar_estado('liberado', 'system_release_scheduler')
                # Reposicionar la fecha_liberacion a la original (el row ya está
                # locked via select_for_update arriba) si difiere de la now()
                # que dejó el FSM.
                if (
                    original_fecha_liberacion is not None
                    and container.fecha_liberacion != original_fecha_liberacion
                ):
                    container.fecha_liberacion = original_fecha_liberacion
                    container.save(update_fields=['fecha_liberacion'])
                    logger.info(
                        'release_due_containers fecha_liberacion preserved container_id=%s fecha=%s',
                        getattr(container, 'container_id', None),
                        original_fecha_liberacion.isoformat(),
                    )
                released += 1
        self.stdout.write(self.style.SUCCESS(f'Liberaciones aplicadas: {released}'))
