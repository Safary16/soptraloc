"""Utilidades para el conteo de contenedores vacíos por centro de distribución."""
from collections import OrderedDict
from dataclasses import dataclass
import unicodedata
from typing import Dict, Iterable

from django.db.models import Count, Q

from apps.containers.models import Container


# Centros de distribución conocidos y su forma canónica
CD_LABELS: Dict[str, str] = OrderedDict({
    "CD_QUILICURA": "CD Quilicura",
    "CD_CAMPOS": "CD Campos",
    "CD_MADERO": "CD Puerto Madero",
    "CD_PENON": "CD El Peñón",
})

SYNONYM_CODES: Dict[str, str] = {
    "CD_EL_PENON": "CD_PENON",
    "CD_PUERTO_MADERO": "CD_MADERO",
    "CD_CAMPOS_DE_CHILE": "CD_CAMPOS",
    "CD_CAMPOS_DE_CHILE_-_PUDAHUEL": "CD_CAMPOS",
}

# Estados que representan contenedores vacíos disponibles en un CD
EMPTY_STATUSES = {"DESCARGADO_CD", "DISPONIBLE_DEVOLUCION"}


@dataclass(frozen=True)
class EmptyInventoryRow:
    code: str
    label: str
    empty_count: int

    def as_dict(self) -> Dict[str, object]:
        return {
            "code": self.code,
            "label": self.label,
            "empty_count": self.empty_count,
        }


def _normalize_cd_value(raw_value: str | None) -> str | None:
    if not raw_value:
        return None
    normalized = raw_value.strip().upper()
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace(" ", "_")
    normalized = normalized.replace("-", "_")
    if normalized in SYNONYM_CODES:
        return SYNONYM_CODES[normalized]
    if normalized.startswith("CD_"):
        return normalized
    for code in CD_LABELS.keys():
        if normalized in {code, code.replace("_", ""), code.replace("CD_", "CD ")}:  # type: ignore[arg-type]
            return code
    return normalized


def _ensure_known_codes(counts: Dict[str, int]) -> Iterable[EmptyInventoryRow]:
    for code, label in CD_LABELS.items():
        yield EmptyInventoryRow(code=code, label=label, empty_count=counts.get(code, 0))


def get_empty_inventory_by_cd() -> Iterable[EmptyInventoryRow]:
    """Calcula el número de contenedores vacíos por CD."""
    qs = (
        Container.objects.filter(
            Q(status__in=EMPTY_STATUSES) | Q(status="FINALIZADO", current_position__startswith="CD_")
        )
        .exclude(cd_location__isnull=True)
        .exclude(cd_location="")
    )

    raw_counts: Dict[str, int] = {}

    for entry in qs.values("cd_location").annotate(total=Count("id")):
        code = _normalize_cd_value(entry["cd_location"])
        if not code:
            continue
        raw_counts[code] = raw_counts.get(code, 0) + entry["total"]

    return _ensure_known_codes(raw_counts)
