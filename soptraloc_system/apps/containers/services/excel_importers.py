from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Iterable, List, Optional, Sequence

import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.containers.models import Agency, Container, ShippingLine, Vessel
from apps.containers.services.status_utils import normalize_status
from apps.core.models import Company
from apps.drivers.models import Alert, Assignment, Driver, Location, TimeMatrix

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column normalization maps
# ---------------------------------------------------------------------------
MANIFEST_COLUMN_MAP = {
    "naveconfirmado": "vessel_name",
    "viajeconfirmado": "voyage",
    "etaconfirmada": "eta",
    "destino": "port",
    "containernumbers": "container_number",
    "containersize": "container_type",
    "containerseal": "seal_number",
    "weightkgs": "weight",
    "vendor": "vendor",
    "division": "division",
    "carrier": "carrier",
    "agencia": "agency",
}

RELEASE_COLUMN_MAP = {
    "mn": "vessel_name",
    "m/n": "vessel_name",
    "contenedor": "container_number",
    "horasalida": "release_time",
    "hora": "release_time",
    "fechasalida": "release_date",
    "fecha": "release_date",
    "devolucionvacio": "empty_return",
    "almacen": "warehouse",
    "transportes": "transport_company",
    "pesounidades": "cargo_weight",
    "peso": "cargo_weight",
    "pesokg": "cargo_weight",
    "pesokgs": "cargo_weight",
    "tipoconttemperat": "container_type",
    "tipoconttemperatura": "container_type",
}

PROGRAM_COLUMN_MAP = {
    "contenedor": "container_number",
    "destino": "cd_location",
    "cd": "cd_location",
    "bodega": "cd_location",
    "fechadespacho": "scheduled_date",
    "fechadeprogramacion": "scheduled_date",
    "fechaprogramacion": "scheduled_date",
    "fecha": "scheduled_date",
    "horaprogramacion": "scheduled_time",
    "hora": "scheduled_time",
    "demurrage": "demurrage_date",
    "fechademurrage": "demurrage_date",
    "tipocontenedor": "container_type",
    "tipocont": "container_type",
    "tipo": "container_type",
    "med": "container_size",
    "deposito": "deposit_return",
    "devolucion": "deposit_return",
    "nave": "vessel_name",
    "referencia": "reference",
    "producto": "product",
}

PORT_LOCATION_MAP = {
    "SAN ANTONIO": {
        "position_code": "CLEP",
        "display": "CLEP SAI",
        "city": "San Antonio",
        "driver_code": "CLEP_SAI",
    },
    "VALPARAISO": {
        "position_code": "ZEAL",
        "display": "ZEAL VAP",
        "city": "Valparaíso",
        "driver_code": "ZEAL_VAP",
    },
}

DEMURRAGE_ALERT_THRESHOLD_DAYS = 2


# ---------------------------------------------------------------------------
# Structured responses
# ---------------------------------------------------------------------------
@dataclass
class ImportSummary:
    file_name: str
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)

    def record_error(self, row_index: int, message: str) -> None:
        self.errors.append(f"Fila {row_index}: {message}")

    def as_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": list(self.errors),
        }


class ImporterError(Exception):
    """Error controlado para flujos de importación."""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _normalize_header(value: object) -> str:
    if value is None:
        return ""
    value = str(value).replace("\ufeff", "").strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", "", value.lower())
    return normalized


def _log_column_mapping(df: pd.DataFrame, column_map: dict, file_type: str) -> None:
    """Log which columns were found and mapped for debugging"""
    logger.info(f"=== Análisis de columnas para archivo {file_type} ===")
    
    # Columnas originales
    logger.info(f"Columnas originales: {list(df.columns)}")
    
    # Columnas normalizadas
    normalized = {col: _normalize_header(col) for col in df.columns}
    logger.info(f"Columnas normalizadas: {normalized}")
    
    # Mapping encontrado
    reverse_map = {v: k for k, v in column_map.items()}
    found_mappings = {}
    for col in df.columns:
        norm = _normalize_header(col)
        if norm in reverse_map:
            found_mappings[col] = reverse_map[norm]
    
    logger.info(f"Columnas mapeadas exitosamente: {found_mappings}")
    logger.info("=" * 60)


def _clean_str(value: Optional[str]) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_cd_location(value: Optional[str]) -> str:
    """
    Normaliza el formato de CD/Bodega.
    Ejemplos:
        "6020 - PEÑÓN" -> "PEÑÓN"
        "QUILICURA" -> "QUILICURA"
        "6030 - QUILICURA" -> "QUILICURA"
    """
    if not value:
        return ""
    cleaned = _clean_str(value)
    # Si tiene formato "código - nombre", extraer solo el nombre
    if " - " in cleaned:
        parts = cleaned.split(" - ", 1)
        if len(parts) == 2:
            return parts[1].strip().upper()
    return cleaned.upper()


def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    if value is None or str(value).strip() == "":
        return None
    cleaned = re.sub(r"[^0-9,.-]", "", str(value))
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Wrapper para DateTimeParser.parse_date compartido"""
    from apps.containers.services.utils import DateTimeParser
    return DateTimeParser.parse_date(value)


def _parse_time(value: Optional[str]) -> Optional[time]:
    """Wrapper para DateTimeParser.parse_time compartido"""
    from apps.containers.services.utils import DateTimeParser
    return DateTimeParser.parse_time(value)


def normalize_container_number(raw: Optional[str]) -> str:
    """Normaliza número de contenedor usando ContainerNumberFormatter compartido"""
    from apps.containers.services.utils import ContainerNumberFormatter
    if not raw:
        return ""
    return ContainerNumberFormatter.format(str(raw))


def _container_variants(number: str) -> Sequence[str]:
    compact = number.replace(" ", "").replace("-", "")
    variants = {number, compact}
    if len(compact) >= 11:
        variants.add(f"{compact[:4]} {compact[4:10]}-{compact[10]}")
    return list(variants)


def match_existing_container(container_number: str) -> Optional[Container]:
    for variant in _container_variants(container_number):
        container = Container.objects.filter(container_number__iexact=variant).first()
        if container:
            return container
    return None


def _get_or_create_company(name: Optional[str], user: User) -> Company:
    """Wrapper para EntityFactory.get_or_create_company con user"""
    from apps.containers.services.utils import EntityFactory
    cleaned = _clean_str(name) or "CLIENTE DEMO"
    return EntityFactory.get_or_create_company(cleaned, user)


def _get_or_create_shipping_line(name: Optional[str], user: User) -> ShippingLine:
    """Wrapper para EntityFactory.get_or_create_shipping_line con user"""
    from apps.containers.services.utils import EntityFactory
    cleaned = _clean_str(name) or "Sin Especificar"
    return EntityFactory.get_or_create_shipping_line(cleaned, user)


def _get_or_create_vessel(name: Optional[str], shipping_line: ShippingLine, user: User) -> Optional[Vessel]:
    """Wrapper para EntityFactory.get_or_create_vessel con user"""
    from apps.containers.services.utils import EntityFactory
    cleaned = _clean_str(name)
    if not cleaned:
        return None
    return EntityFactory.get_or_create_vessel(cleaned, shipping_line, user)


def _get_or_create_agency(name: Optional[str], user: User) -> Optional[Agency]:
    """Wrapper para EntityFactory.get_or_create_agency con user"""
    from apps.containers.services.utils import EntityFactory
    cleaned = _clean_str(name)
    if not cleaned:
        return None
    return EntityFactory.get_or_create_agency(cleaned, user)


def _get_or_create_location(name: str, code: str = None, city: str = '') -> Location:
    """
    Obtiene o crea una ubicación. 
    Usa primero el código si está disponible, sino busca por nombre.
    """
    if code:
        location = Location.objects.filter(code=code).first()
        if location:
            return location
    
    location = Location.objects.filter(name__iexact=name).first()
    if location:
        return location
    
    # Crear nueva ubicación
    if not code:
        # Generar código a partir del nombre
        code = name.upper().replace(' ', '_')[:20]
        # Asegurar unicidad
        base_code = code
        counter = 1
        while Location.objects.filter(code=code).exists():
            code = f"{base_code}_{counter}"
            counter += 1
    
    return Location.objects.create(
        name=name,
        code=code,
        address=name,
        city=city or '',
        region='Metropolitana',
        country='Chile'
    )


def _derive_container_type(raw_type: Optional[str]) -> str:
    if not raw_type:
        return "40ft"
    cleaned = re.sub(r"[^A-Z0-9]", "", str(raw_type).upper())
    if "45" in cleaned:
        return "45ft"
    if "20" in cleaned:
        return "20ft"
    if "HC" in cleaned or "HQ" in cleaned:
        return "40hc"
    if "RF" in cleaned or "REEFER" in cleaned:
        return "reefer"
    return "40ft"


def _attach_operational_location(container: Container, user: User) -> None:
    port = _clean_str(container.port).upper()
    meta = PORT_LOCATION_MAP.get(port)
    if not meta:
        return

    container.current_position = meta["position_code"]
    container.position_status = "warehouse"
    container.current_location = _get_or_create_location(meta["display"], meta["driver_code"], meta["city"])


# ---------------------------------------------------------------------------
# Import workflows
# ---------------------------------------------------------------------------
def import_vessel_manifest(files: Iterable[BytesIO], user: User) -> List[ImportSummary]:
    summaries: List[ImportSummary] = []
    for uploaded in files:
        filename = getattr(uploaded, "name", "manifest.xlsx")
        summary = ImportSummary(file_name=filename)
        try:
            uploaded.seek(0)
            df = pd.read_excel(uploaded, dtype=str)
        except Exception as exc:
            summary.record_error(0, f"No se pudo leer el archivo: {exc}")
            summaries.append(summary)
            continue

        column_lookup = {_normalize_header(col): col for col in df.columns}
        if "containernumbers" not in column_lookup:
            summary.record_error(0, "No se encontró la columna de contenedores")
            summaries.append(summary)
            continue

        for idx, row in df.iterrows():
            raw_container = row.get(column_lookup["containernumbers"])
            container_number = normalize_container_number(raw_container)
            if not container_number:
                summary.skipped += 1
                continue

            try:
                with transaction.atomic():
                    container = match_existing_container(container_number)
                    created = container is None
                    if created:
                        container = Container(container_number=container_number)
                        container.created_by = user

                    # Vendor es el dueño de la mercancía (ej: ANIKET METALS)
                    vendor_name = row.get(column_lookup.get("vendor")) or row.get(column_lookup.get("division"))
                    vendor_company = _get_or_create_company(vendor_name, user)
                    
                    # Cliente es quien solicita el servicio de transporte (Cliente Demo)
                    client_company = _get_or_create_company("CLIENTE DEMO", user)
                    
                    shipping_line = _get_or_create_shipping_line(row.get(column_lookup.get("carrier")), user)
                    vessel = _get_or_create_vessel(row.get(column_lookup.get("naveconfirmado")), shipping_line, user)
                    agency = _get_or_create_agency(row.get(column_lookup.get("agencia")), user)

                    container.owner_company = vendor_company  # Dueño de mercancía
                    container.client = client_company  # Cliente del servicio de transporte
                    container.shipping_line = shipping_line
                    container.vessel = vessel
                    container.agency = agency
                    container.container_type = _derive_container_type(row.get(column_lookup.get("containersize")))
                    container.seal_number = _clean_str(row.get(column_lookup.get("containerseal")))
                    weight_decimal = _parse_decimal(row.get(column_lookup.get("weightkgs")))
                    if weight_decimal is not None:
                        container.total_weight = weight_decimal
                    container.port = _clean_str(row.get(column_lookup.get("destino")))
                    container.eta = _parse_date(row.get(column_lookup.get("etaconfirmada")))
                    container.status = normalize_status("POR_ARRIBAR")
                    container.position_status = "floor"
                    container.current_position = "EN_RUTA"
                    container.service_type = container.service_type or "INDIRECTO_DEPOSITO"
                    container.updated_by = user
                    container.save()

                    if created:
                        summary.created += 1
                    else:
                        summary.updated += 1
            except Exception as exc:  # pragma: no cover - logged for troubleshooting
                logger.exception("Error importando contenedor %s", container_number)
                summary.record_error(idx + 2, str(exc))

        summaries.append(summary)

    return summaries


def _load_release_dataframe(uploaded: BytesIO) -> pd.DataFrame:
    uploaded.seek(0)
    raw = pd.read_excel(uploaded, header=None, dtype=str)
    header_idx = None
    for idx, row in raw.iterrows():
        normalized = [_normalize_header(cell) for cell in row.tolist() if cell is not None]
        if "contenedor" in normalized and ("fechasalida" in normalized or "fecha" in normalized):
            header_idx = idx
            break
    if header_idx is None:
        raise ImporterError("No se encontró la fila de cabeceras en el archivo de liberaciones")

    header_row = raw.iloc[header_idx]
    data = raw.iloc[header_idx + 1 :].copy()
    data.columns = header_row
    data = data.dropna(how="all")
    return data


def apply_release_schedule(uploaded: BytesIO, user: User) -> ImportSummary:
    filename = getattr(uploaded, "name", "liberaciones.xlsx")
    summary = ImportSummary(file_name=filename)
    try:
        df = _load_release_dataframe(uploaded)
    except Exception as exc:
        summary.record_error(0, f"No se pudo procesar el archivo: {exc}")
        return summary

    column_lookup = {_normalize_header(col): col for col in df.columns}
    
    # Debug: mostrar mapeo de columnas
    _log_column_mapping(df, RELEASE_COLUMN_MAP, "LIBERACION")
    if "contenedor" not in column_lookup:
        summary.record_error(0, "No se encontró la columna de contenedores")
        return summary

    for idx, row in df.iterrows():
        container_number = normalize_container_number(row.get(column_lookup["contenedor"]))
        if not container_number:
            summary.skipped += 1
            continue

        container = match_existing_container(container_number)
        if not container:
            summary.record_error(idx + 2, f"Contenedor {container_number} no existe en el sistema")
            summary.skipped += 1
            continue

        try:
            with transaction.atomic():
                # Intentar diferentes columnas para fecha
                date_value = (
                    row.get(column_lookup.get("fechasalida")) 
                    or row.get(column_lookup.get("fecha"))
                    or row.get(column_lookup.get("fechaliberacion"))
                )
                release_date = _parse_date(date_value)
                
                # Intentar diferentes columnas para hora
                time_value = (
                    row.get(column_lookup.get("horasalida")) 
                    or row.get(column_lookup.get("hora"))
                    or row.get(column_lookup.get("horaliberacion"))
                )
                release_time = _parse_time(time_value)

                logger.info(
                    "Procesando liberación %s: fecha_raw=%s -> %s, hora_raw=%s -> %s",
                    container_number, date_value, release_date, time_value, release_time
                )

                if release_date:
                    container.release_date = release_date
                if release_time:
                    container.release_time = release_time

                # ⚠️ VALIDACIÓN CRÍTICA: Solo cambiar a LIBERADO si la fecha ya pasó
                today = timezone.now().date()
                if release_date and release_date > today:
                    # Fecha futura - mantener en POR_ARRIBAR o estado actual
                    logger.info(
                        "Contenedor %s: fecha liberación futura (%s). Manteniendo estado %s",
                        container.container_number, release_date, container.status
                    )
                    # Solo actualizar la fecha pero no el estado
                else:
                    # Fecha actual o pasada - cambiar a LIBERADO
                    container.status = normalize_status("LIBERADO")
                    container.position_status = "warehouse"
                    if not container.current_position or container.current_position == "EN_RUTA":
                        _attach_operational_location(container, user)

                depot = _clean_str(row.get(column_lookup.get("devolucionvacio")))
                if depot:
                    container.deposit_return = depot
                warehouse = _clean_str(row.get(column_lookup.get("almacen")))
                if warehouse:
                    container.storage_location = warehouse
                
                # Extraer peso de carga
                cargo_weight = _parse_decimal(
                    row.get(column_lookup.get("pesounidades"))
                    or row.get(column_lookup.get("peso"))
                    or row.get(column_lookup.get("pesokg"))
                    or row.get(column_lookup.get("pesokgs"))
                )
                if cargo_weight:
                    container.cargo_weight = cargo_weight

                container.updated_by = user
                container.save()
                summary.updated += 1
        except Exception as exc:  # pragma: no cover - logged for troubleshooting
            logger.exception("Error actualizando liberación para %s", container_number)
            summary.record_error(idx + 2, str(exc))

    return summary


def _load_program_dataframe(uploaded: BytesIO) -> pd.DataFrame:
    uploaded.seek(0)
    try:
        df = pd.read_excel(uploaded, dtype=str)
    except ValueError:
        uploaded.seek(0)
        df = pd.read_csv(uploaded, dtype=str, sep=";|\t", engine="python")
    return df.dropna(how="all")


def apply_programming(uploaded: BytesIO, user: User) -> ImportSummary:
    filename = getattr(uploaded, "name", "programacion.xlsx")
    summary = ImportSummary(file_name=filename)
    try:
        df = _load_program_dataframe(uploaded)
    except Exception as exc:
        summary.record_error(0, f"No se pudo leer el archivo: {exc}")
        return summary

    column_lookup = {_normalize_header(col): col for col in df.columns}
    
    # Debug: mostrar mapeo de columnas
    _log_column_mapping(df, PROGRAM_COLUMN_MAP, "PROGRAMACION")
    
    if "contenedor" not in column_lookup:
        summary.record_error(0, "No se encontró la columna de contenedores")
        return summary

    for idx, row in df.iterrows():
        container_number = normalize_container_number(row.get(column_lookup["contenedor"]))
        if not container_number:
            summary.skipped += 1
            continue

        container = match_existing_container(container_number)
        if not container:
            summary.record_error(idx + 2, f"Contenedor {container_number} no existe en el sistema")
            continue

        try:
            with transaction.atomic():
                # Intentar diferentes columnas para fecha programada
                date_value = (
                    row.get(column_lookup.get("fechadespacho"))
                    or row.get(column_lookup.get("fechaprogramacion"))
                    or row.get(column_lookup.get("fechadeprogramacion"))
                    or row.get(column_lookup.get("fecha"))
                )
                scheduled_date = _parse_date(date_value)
                
                # Intentar diferentes columnas para hora programada
                time_value = (
                    row.get(column_lookup.get("horaprogramacion")) 
                    or row.get(column_lookup.get("hora"))
                    or row.get(column_lookup.get("horadespacho"))
                )
                scheduled_time = _parse_time(time_value)
                
                # Intentar diferentes columnas para CD/destino
                cd_value = (
                    row.get(column_lookup.get("destino")) 
                    or row.get(column_lookup.get("cd")) 
                    or row.get(column_lookup.get("bodega"))
                    or row.get(column_lookup.get("cdlocation"))
                )
                cd_location = _normalize_cd_location(cd_value)
                
                logger.info(
                    "Procesando programación %s: fecha_raw=%s -> %s, hora_raw=%s -> %s, cd_raw=%s -> %s",
                    container_number, date_value, scheduled_date, time_value, scheduled_time, cd_value, cd_location
                )
                demurrage_date = _parse_date(row.get(column_lookup.get("demurrage")) or row.get(column_lookup.get("fechademurrage")))
                deposit_return = _clean_str(row.get(column_lookup.get("deposito")) or row.get(column_lookup.get("devolucion")))
                container_type = _derive_container_type(
                    row.get(column_lookup.get("tipocontenedor")) or row.get(column_lookup.get("tipocont"))
                )

                if scheduled_date:
                    container.scheduled_date = scheduled_date
                if scheduled_time:
                    container.scheduled_time = scheduled_time
                if cd_location:
                    container.cd_location = cd_location
                if container_type:
                    container.container_type = container_type
                if demurrage_date:
                    container.demurrage_date = demurrage_date
                if deposit_return:
                    container.deposit_return = deposit_return

                container.status = normalize_status("PROGRAMADO")
                container.updated_by = user
                container.save()

                _attach_operational_location(container, user)
                create_demurrage_alert_if_needed(container)
                assign_driver_by_location(container, user)
                summary.updated += 1
        except Exception as exc:  # pragma: no cover - logged for troubleshooting
            logger.exception("Error aplicando programación a %s", container_number)
            summary.record_error(idx + 2, str(exc))

    return summary


# ---------------------------------------------------------------------------
# Post-import automation helpers
# ---------------------------------------------------------------------------
def assign_driver_by_location(container: Container, user: User) -> Optional[Driver]:
    if container.conductor_asignado_id:
        return container.conductor_asignado

    from apps.drivers.views import (
        _assign_driver_to_container,
        _compute_scheduled_datetime,
        _has_schedule_conflict,
        _resolve_assignment_locations,
    )

    preferred_types = preferred_driver_types(container)
    if not preferred_types:
        return None

    today = timezone.localdate()
    scheduled_datetime = _compute_scheduled_datetime(container)

    available_drivers = Driver.objects.filter(
        is_active=True,
        estado="OPERATIVO",
        contenedor_asignado__isnull=True,
        tipo_conductor__in=preferred_types,
        ultimo_registro_asistencia=today,
        hora_ingreso_hoy__isnull=False,
    ).order_by("tiempo_en_ubicacion")

    for driver in available_drivers:
        origin, destination = _resolve_assignment_locations(driver, container)
        duration = _estimate_duration(origin, destination)
        if _has_schedule_conflict(driver, scheduled_datetime, duration):
            continue
        try:
            assignment = _assign_driver_to_container(container, driver, user, scheduled_datetime)
            logger.info(
                "Conductor %s asignado automáticamente a contenedor %s",
                driver.nombre,
                container.container_number,
            )
            return assignment.driver
        except ValueError:
            continue
    return None


def preferred_driver_types(container: Container) -> List[str]:
    current = (container.current_position or "").upper()
    deposit = (container.deposit_return or "").upper()
    cd_location = (container.cd_location or "").upper()

    if current in {"CLEP", "ZEAL"} or any(suffix in deposit for suffix in ("VAP", "SAI")):
        return ["TRONCO", "TRONCO_PM"]
    if current == "CCTI" or cd_location.startswith("CD"):
        return ["LOCALERO", "LEASING"]
    return ["TRONCO", "TRONCO_PM", "LEASING", "LOCALERO"]


def _estimate_duration(origin: Optional[Location], destination: Optional[Location]) -> int:
    """Estima la duración de una ruta basada en la matriz de tiempos."""
    if origin and destination:
        try:
            matrix = TimeMatrix.objects.get(from_location=origin, to_location=destination)
            return matrix.get_total_time()
        except TimeMatrix.DoesNotExist:
            return 120
    return 120


def create_demurrage_alert_if_needed(container: Container) -> Optional[Alert]:
    if not container.demurrage_date:
        return None
    today = timezone.localdate()
    days_until = (container.demurrage_date - today).days
    if days_until > DEMURRAGE_ALERT_THRESHOLD_DAYS:
        return None

    alert, created = Alert.objects.get_or_create(
        tipo="DEMURRAGE_PROXIMO",
        container=container,
        defaults={
            "prioridad": "ALTA" if days_until >= 0 else "CRITICA",
            "titulo": f"Demurrage próximo para {container.container_number}",
            "mensaje": f"El contenedor debe devolverse antes de {container.demurrage_date.strftime('%d/%m/%Y')}",
        },
    )
    if not created:
        alert.is_active = True
        alert.prioridad = "ALTA" if days_until >= 0 else "CRITICA"
        alert.mensaje = f"El contenedor debe devolverse antes de {container.demurrage_date.strftime('%d/%m/%Y')}"
        alert.save(update_fields=["is_active", "prioridad", "mensaje", "updated_at"])
    return alert


def export_liberated_containers(reference_date: Optional[date] = None, include_future: bool = False) -> BytesIO:
    """
    Exporta contenedores liberados a Excel con validación de fechas.
    
    Args:
        reference_date: Fecha de referencia (default: hoy)
        include_future: Si True, incluye contenedores con liberación futura
    """
    from django.db import models as django_models
    
    if reference_date is None:
        reference_date = timezone.now().date()
    
    liberated = Container.objects.filter(
        status__in=[normalize_status("LIBERADO"), normalize_status("PROGRAMADO")]
    )
    
    # Filtrar por fecha de liberación si no se incluyen futuros
    if not include_future:
        liberated = liberated.filter(
            django_models.Q(release_date__isnull=True) | django_models.Q(release_date__lte=reference_date)
        )
    
    liberated = liberated.order_by("scheduled_date", "container_number")

    rows = []
    for container in liberated:
        # Determinar si la liberación es futura
        is_future = container.release_date and container.release_date > reference_date
        
        rows.append(
            {
                "Contenedor": container.container_number,
                "Cliente": container.owner_company.name if container.owner_company else "",
                "Puerto / Origen": container.port or "",
                "ETA": container.eta.strftime("%d/%m/%Y") if container.eta else "",
                "Liberación": container.release_date.strftime("%d/%m/%Y") if container.release_date else "",
                "Hora Liberación": container.release_time.strftime("%H:%M") if container.release_time else "",
                "Liberación Futura": "SÍ" if is_future else "NO",
                "Demurrage": container.demurrage_date.strftime("%d/%m/%Y") if container.demurrage_date else "",
                "CD Destino": container.cd_location or "",
                "Programado Para": container.scheduled_date.strftime("%d/%m/%Y") if container.scheduled_date else "",
                "Hora Programada": container.scheduled_time.strftime("%H:%M") if container.scheduled_time else "",
                "Ubicación Actual": container.current_position or "",
                "Depósito Retorno": container.deposit_return or "",
                "Estado": container.get_status_display() if hasattr(container, "get_status_display") else container.status,
            }
        )

    df = pd.DataFrame(rows)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name="Liberados")
    output.seek(0)
    return output


def update_operational_learning(container: Container) -> None:
    assignment = Assignment.objects.filter(container=container).order_by("-fecha_asignacion").first()
    if not assignment or not assignment.origen or not assignment.destino:
        return

    travel_minutes = None
    unload_minutes = None

    if container.tiempo_inicio_ruta and container.tiempo_llegada:
        delta = container.tiempo_llegada - container.tiempo_inicio_ruta
        travel_minutes = max(int(delta.total_seconds() // 60), 1)

    if container.tiempo_descarga and container.tiempo_llegada:
        delta = container.tiempo_descarga - container.tiempo_llegada
        unload_minutes = max(int(delta.total_seconds() // 60), 0)

    if travel_minutes is None and unload_minutes is None:
        return

    matrix, _ = TimeMatrix.objects.get_or_create(
        from_location=assignment.origen,
        to_location=assignment.destino,
        defaults={
            "travel_time": travel_minutes or 120,
            "loading_time": 0,
            "unloading_time": unload_minutes or 0,
        },
    )

    if travel_minutes is not None:
        matrix.update_historical_data(travel_minutes)
    if unload_minutes is not None:
        matrix.unloading_time = unload_minutes
        matrix.save(update_fields=["unloading_time", "updated_at"])


__all__ = [
    "ImportSummary",
    "ImporterError",
    "import_vessel_manifest",
    "apply_release_schedule",
    "apply_programming",
    "assign_driver_by_location",
    "create_demurrage_alert_if_needed",
    "export_liberated_containers",
    "update_operational_learning",
]
