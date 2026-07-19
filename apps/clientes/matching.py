"""Pareo seguro de nombres de cliente provenientes de planillas operativas."""
import re
import unicodedata

from .models import ClienteEmpresa


def normalize_customer_key(value):
    """Normaliza tildes, puntuación y espacios sin hacer pareos difusos riesgosos."""
    text = '' if value is None else str(value)
    text = ''.join(
        char for char in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(char)
    ).upper().strip()
    return re.sub(r'[^A-Z0-9]+', '', text)


def resolve_customer(value):
    """Retorna la empresa activa por nombre o RUT canónico; exige coincidencia única."""
    key = normalize_customer_key(value)
    if not key:
        raise ValueError('Cliente vacío en la planilla de embarque.')
    matches = [
        company for company in ClienteEmpresa.objects.filter(activo=True)
        if key in {
            normalize_customer_key(company.nombre),
            normalize_customer_key(company.rut),
        }
    ]
    if not matches:
        raise ValueError(
            f"Cliente '{str(value).strip()}' no está registrado. "
            'Créelo o corrige su nombre/RUT antes de reimportar; no se creó automáticamente.'
        )
    if len(matches) > 1:
        raise ValueError(f"Cliente '{str(value).strip()}' es ambiguo; revise nombres y RUT registrados.")
    return matches[0]
