from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from apps.drivers.models import Alert


DEMURRAGE_ALERT_THRESHOLD_DAYS = 2
DEMURRAGE_ALERT_TYPES = ("DEMURRAGE_PROXIMO", "DEMURRAGE_VENCIDO")


@dataclass
class DemurrageAlertResult:
    alert: Alert
    was_created: bool
    alert_type: str
    days_until: int


def _resolve_existing_alerts(container, *, resolved_by=None) -> int:
    """Marca como resueltas las alertas activas de demurrage para un contenedor."""
    from apps.drivers.models import Alert

    now = timezone.now()
    updates = {
        "is_active": False,
        "fecha_resolucion": now,
    }
    if resolved_by is not None:
        updates["resuelto_por"] = resolved_by

    queryset = Alert.objects.filter(
        container=container,
        tipo__in=DEMURRAGE_ALERT_TYPES,
        is_active=True,
    )
    count = queryset.count()
    if count:
        queryset.update(**updates)
    return count


def create_demurrage_alert_if_needed(container, *, resolved_by=None) -> Optional[DemurrageAlertResult]:
    """Crea o actualiza la alerta de demurrage apropiada para el contenedor."""
    from apps.drivers.models import Alert

    if not container.demurrage_date:
        _resolve_existing_alerts(container, resolved_by=resolved_by)
        return None

    today = timezone.localdate()
    days_until = (container.demurrage_date - today).days

    if days_until > DEMURRAGE_ALERT_THRESHOLD_DAYS:
        _resolve_existing_alerts(container, resolved_by=resolved_by)
        return None

    if days_until >= 0:
        alert_type = "DEMURRAGE_PROXIMO"
        prioridad = "ALTA" if days_until <= 1 else "MEDIA"
        titulo = f"Demurrage próximo para {container.container_number}"
        mensaje = (
            "El contenedor debe devolverse antes de "
            f"{container.demurrage_date.strftime('%d/%m/%Y')}"
        )
    else:
        alert_type = "DEMURRAGE_VENCIDO"
        prioridad = "CRITICA"
        days_overdue = abs(days_until)
        titulo = f"URGENTE: Demurrage vencido - {container.container_number}"
        mensaje = (
            "⚠️ CRÍTICO: Contenedor "
            f"{container.container_number} lleva {days_overdue} día(s) en demurrage. "
            "Priorizar devolución inmediata."
        )

    alert, created = Alert.objects.get_or_create(
        container=container,
        tipo=alert_type,
        defaults={
            "prioridad": prioridad,
            "titulo": titulo,
            "mensaje": mensaje,
            "driver": container.conductor_asignado,
        },
    )

    alert.prioridad = prioridad
    alert.titulo = titulo
    alert.mensaje = mensaje
    alert.is_active = True
    alert.fecha_resolucion = None
    alert.driver = container.conductor_asignado

    update_fields = [
        "prioridad",
        "titulo",
        "mensaje",
        "is_active",
        "fecha_resolucion",
        "driver",
    ]

    if resolved_by is not None:
        alert.resuelto_por = resolved_by
        update_fields.append("resuelto_por")

    alert.save(update_fields=update_fields)

    now = timezone.now()
    Alert.objects.filter(
        container=container,
        tipo__in=DEMURRAGE_ALERT_TYPES,
        is_active=True,
    ).exclude(pk=alert.pk).update(
        is_active=False,
        fecha_resolucion=now,
        resuelto_por=resolved_by,
    )

    return DemurrageAlertResult(
        alert=alert,
        was_created=created,
        alert_type=alert_type,
        days_until=days_until,
    )


def resolve_demurrage_alerts(container, *, resolved_by=None) -> int:
    """API pública para resolver alertas de demurrage."""
    return _resolve_existing_alerts(container, resolved_by=resolved_by)