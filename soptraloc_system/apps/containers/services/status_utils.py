"""Utilities for container status normalization and reporting."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

DEFAULT_STATUS = "PROGRAMADO"

# Canonical statuses that the UI and business logic expect
CANONICAL_STATUSES: Dict[str, str] = {
    "PROGRAMADO": "PROGRAMADO",
    "EN_PROCESO": "EN_PROCESO",
    "EN_TRANSITO": "EN_TRANSITO",
    "LIBERADO": "LIBERADO",
    "DESCARGADO": "DESCARGADO",
    "EN_SECUENCIA": "EN_SECUENCIA",
    "ASIGNADO": "ASIGNADO",
    "EN_RUTA": "EN_RUTA",
    "ARRIBADO": "ARRIBADO",
    "FINALIZADO": "FINALIZADO",
    "POR_ARRIBAR": "POR_ARRIBAR",
    "SECUENCIADO": "SECUENCIADO",
    "TRG": "TRG",
}

# Aliases coming from historical datasets or CSV variations
STATUS_ALIASES: Dict[str, str] = {
    "": DEFAULT_STATUS,
    "AVAILABLE": "PROGRAMADO",
    "DISPONIBLE": "PROGRAMADO",
    "PROGRAMMED": "PROGRAMADO",
    "LOADING": "EN_PROCESO",
    "EN PROCESO": "EN_PROCESO",
    "IN_TRANSIT": "EN_TRANSITO",
    "IN TRANSIT": "EN_TRANSITO",
    "EN_TRANSITO": "EN_TRANSITO",
    "EN TRANSITO": "EN_TRANSITO",
    "DISPATCHED": "LIBERADO",
    "RELEASED": "LIBERADO",
    "FINISHED": "FINALIZADO",
    "POR ARRIBAR": "POR_ARRIBAR",
    "EN SECUENCIA": "EN_SECUENCIA",
    "TRG": "TRG",
    "FINALIZADO": "FINALIZADO",
    "LIBERADO": "LIBERADO",
    "DESCARGADO": "DESCARGADO",
    "ASIGNADO": "ASIGNADO",
    "EN_RUTA": "EN_RUTA",
    "ARRIBADO": "ARRIBADO",
    "SECUENCIADO": "SECUENCIADO",
}

# Statuses considered "active" for dashboard visibility
ACTIVE_STATUS_CODES: List[str] = [
    "PROGRAMADO",
    "EN_PROCESO",
    "EN_TRANSITO",
    "LIBERADO",
    "DESCARGADO",
    "EN_SECUENCIA",
    "ASIGNADO",
    "EN_RUTA",
]


def related_status_values(status_code: str) -> List[str]:
    """Return all raw values that should map to the given status code."""
    canonical = normalize_status(status_code)
    related = {canonical}
    for alias, target in STATUS_ALIASES.items():
        if normalize_status(target) == canonical or target == canonical:
            if alias:
                related.add(alias)
    return sorted(related)


def active_status_filter_values() -> List[str]:
    """Return all database values that represent active container statuses."""
    values = set()
    for code in ACTIVE_STATUS_CODES:
        values.update(related_status_values(code))
    return sorted(values)


def normalize_status(raw_status: str | None) -> str:
    """Return a canonical status for the given value."""
    if raw_status is None:
        return DEFAULT_STATUS

    value = str(raw_status).strip()
    if not value:
        return DEFAULT_STATUS

    upper_value = value.upper()
    if upper_value in CANONICAL_STATUSES:
        return upper_value
    if upper_value in STATUS_ALIASES:
        return STATUS_ALIASES[upper_value]

    # Default fallback keeps system consistent and avoids invalid values
    return DEFAULT_STATUS


def is_active_status(status: str | None) -> bool:
    """Whether a status should be considered active for operational dashboards."""
    normalized = normalize_status(status)
    return normalized in ACTIVE_STATUS_CODES


@dataclass(frozen=True)
class StatusSummary:
    code: str
    count: int


def summarize_statuses(status_counts: Iterable[tuple[str, int]]) -> List[StatusSummary]:
    """Convert tuples to typed summaries sorted by relevance."""
    summaries = [StatusSummary(code=normalize_status(code), count=count) for code, count in status_counts]
    # Aggregate duplicates after normalization
    aggregated: Dict[str, int] = {}
    for summary in summaries:
        aggregated[summary.code] = aggregated.get(summary.code, 0) + summary.count
    return [StatusSummary(code=code, count=count) for code, count in sorted(aggregated.items())]
