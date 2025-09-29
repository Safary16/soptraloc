from __future__ import annotations

import csv
import io
import re
import unicodedata
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, Optional, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction

from apps.containers.models import Agency, Container, ShippingLine, Vessel
from apps.containers.services.status_utils import normalize_status
from apps.core.models import Company, Location

UserModel = get_user_model()

ENCODING_CANDIDATES = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
FIELD_MAP: Dict[str, str] = {
    "id": "sequence_id",
    "cliente": "client_name",
    "pto": "port",
    "port": "port",
    "eta": "eta",
    "nave": "vessel_name",
    "contenedor": "container_number",
    "status": "status",
    "sello": "seal_number",
    "med": "container_type",
    "medida": "container_type",
    "carga": "cargo_weight",
    "pesototal": "total_weight",
    "terminal": "terminal_name",
    "fechaliberacion": "release_date",
    "fechaliberaci": "release_date",
    "horaliberacion": "release_time",
    "horaliberaci": "release_time",
    "fechaprogramacion": "scheduled_date",
    "fechaprogramaci": "scheduled_date",
    "horaprogramacion": "scheduled_time",
    "horaprogramaci": "scheduled_time",
    "fechaarriboencd": "cd_arrival_date",
    "hora": "cd_arrival_time",
    "cd": "cd_location",
    "fechadesgwhatsappotawero": "discharge_date",
    "horadesg": "discharge_time",
    "fechadev": "return_date",
    "eir": "has_eir",
    "agencia": "agency_name",
    "cianavieralinea": "shipping_line_name",
    "depdev": "deposit_return",
    "diaslibres": "free_days",
    "demurrage": "demurrage_date",
    "sobrestadiaregionxciclo2horas": "overtime_2h",
    "sobrestadiargionxciclo2horas": "overtime_2h",
    "sobreestadiaxciclode4hora": "overtime_4h",
    "description": "cargo_description",
    "almc": "storage_location",
    "diasextrasdealmacenaje": "extra_storage_days",
    "echasis": "chassis_status",
    "tipodeservicio": "service_type",
    "servicioadicional": "additional_service",
    "obs1": "observation_1",
    "obs2": "observation_2",
    "serviciodirecto": "direct_service",
    "fechaact": "last_update_date",
    "horaact": "last_update_time",
    "diascalculados": "calculated_days",
}
CONTAINER_TYPE_MAP = {
    "20": "20ft",
    "20ST": "20st",
    "20STANDAR": "20st",
    "20STANDARD": "20st",
    "40": "40ft",
    "40HC": "40hc",
    "40HQ": "40hc",
    "40HR": "40hr",
    "40HN": "40hn",
    "40H": "40h",
    "45": "45ft",
}
SERVICE_TYPE_MAP = {
    "DIRECTO": "DIRECTO",
    "INDIRECTODEPOSITO": "INDIRECTO_DEPOSITO",
    "INDIRECTO DEPOSITO": "INDIRECTO_DEPOSITO",
    "INDIRECTO": "INDIRECTO_DEPOSITO",
    "REEFER": "REEFER",
}
BOOLEAN_TRUE_VALUES = {"true", "1", "x", "si", "sí", "s", "y", "yes"}
DATE_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%y", "%d-%m-%y"]
TIME_FORMATS = ["%H:%M", "%H:%M:%S", "%I:%M %p"]
DECIMAL_CLEAN_RE = re.compile(r"[^0-9,.-]")
CONTAINER_NUMBER_RE = re.compile(r"[^A-Z0-9]")


class Command(BaseCommand):
    help = "Importa contenedores desde un archivo CSV basado en el formato del Excel de Walmart"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Ruta al archivo CSV a importar")
        parser.add_argument("--user", type=int, default=1, help="ID del usuario que ejecuta la importación")
        parser.add_argument("--dry-run", action="store_true", help="Ejecuta sin guardar cambios")
        parser.add_argument("--truncate", action="store_true", help="Elimina contenedores antes de importar")
        parser.add_argument("--encoding", type=str, help="Forzar un encoding específico")

    def handle(self, *args, **options):
        csv_file_path = Path(options["csv_file"]).resolve()
        user_id = options["user"]
        dry_run = options["dry_run"]
        truncate = options["truncate"]
        encoding = options.get("encoding")

        if not csv_file_path.exists():
            raise CommandError(f"Archivo {csv_file_path} no encontrado")

        user = self.get_user(user_id)
        self.import_file(csv_file_path, user, dry_run=dry_run, truncate=truncate, encoding=encoding)

    def import_file(
        self,
        csv_file_path: Path,
        user: AbstractBaseUser,
        dry_run: bool = False,
        truncate: bool = False,
        encoding: Optional[str] = None,
    ) -> None:
        content = self.read_file(csv_file_path, encoding)

        if truncate and not dry_run:
            total = Container.objects.count()
            Container.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"🧹 Eliminados {total} contenedores antes de importar"))

        self.process_csv(content, user, dry_run)

    def read_file(self, csv_file_path: Path, encoding: Optional[str]) -> str:
        encodings = [encoding] if encoding else ENCODING_CANDIDATES
        last_error: Optional[Exception] = None

        for enc in encodings:
            if not enc:
                continue
            try:
                with csv_file_path.open("r", encoding=enc, errors="replace") as file:
                    return file.read()
            except UnicodeDecodeError as exc:
                last_error = exc
                continue

        if last_error:
            raise CommandError(f"No se pudo decodificar el CSV: {last_error}")
        raise CommandError("No fue posible leer el archivo CSV")

    def process_csv(self, content: str, user: AbstractBaseUser, dry_run: bool) -> None:
        if not content.strip():
            raise CommandError("El archivo CSV está vacío")

        delimiter = ";"
        try:
            delimiter = csv.Sniffer().sniff(content[:4096]).delimiter
        except csv.Error:
            pass

        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        headers = None
        rows = []

        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            if headers is None:
                headers = row
            else:
                rows.append(row)

        if not headers:
            raise CommandError("No se encontraron cabeceras en el CSV")

        fieldnames = self.prepare_fieldnames(headers)
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=delimiter)
        writer.writerow(fieldnames)
        writer.writerows(rows)
        buffer.seek(0)

        dict_reader = csv.DictReader(buffer, delimiter=delimiter)

        created = 0
        updated = 0
        errors = []

        for row_num, row in enumerate(dict_reader, start=2):
            normalized_row = self.normalize_row(row)
            mapped_data = self.map_row(normalized_row)

            if not mapped_data:
                continue

            try:
                with transaction.atomic():
                    container_data = self.process_container_data(mapped_data, user)
                    container_number = container_data.get("container_number")

                    if not container_number:
                        raise ValueError("Número de contenedor inválido o vacío")

                    if dry_run:
                        self.stdout.write(f"[DRY RUN] Procesaría {container_number}")
                        continue

                    container, is_created = self.create_or_update_container(container_data, user)
                    if is_created:
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f"➕ Creado: {container.container_number}"))
                    else:
                        updated += 1
                        self.stdout.write(f"♻️  Actualizado: {container.container_number}")

            except Exception as exc:
                error_msg = f"Error en fila {row_num}: {exc}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nImportación completada:\n- Contenedores creados: {created}\n- Contenedores actualizados: {updated}\n- Errores: {len(errors)}"
            )
        )

        if errors:
            self.stdout.write(self.style.ERROR("\nErrores encontrados:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))

    def prepare_fieldnames(self, headers: Iterable[str]) -> Iterable[str]:
        fieldnames = []
        unused_index = 1

        for header in headers:
            normalized = self.normalize_header(header)
            if not normalized:
                fieldnames.append(f"unused_{unused_index}")
                unused_index += 1
            else:
                fieldnames.append(normalized)
        return fieldnames

    def normalize_row(self, row: Dict[str, str]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key, value in row.items():
            if not key or key.startswith("unused_"):
                continue
            normalized[key] = (value or "").strip()
        return normalized

    def map_row(self, row: Dict[str, str]) -> Dict[str, str]:
        mapped: Dict[str, str] = {}
        for normalized_key, value in row.items():
            field_name = FIELD_MAP.get(normalized_key)
            if field_name:
                mapped[field_name] = value
        return mapped

    def normalize_name(self, value: Optional[str]) -> str:
        if not value:
            return ""
        normalized = unicodedata.normalize("NFKC", value.strip())
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def clean_identifier(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_chars = []
        for char in normalized:
            if unicodedata.combining(char):
                continue
            if char.isalnum():
                ascii_chars.append(char.upper())
        return "".join(ascii_chars)

    def generate_unique_code(
        self,
        model: Type[models.Model],
        base_value: str,
        max_length: int,
        prefix: str,
        field: str = "code",
    ) -> str:
        cleaned_base = self.clean_identifier(base_value) if base_value else ""
        cleaned_prefix = self.clean_identifier(prefix) or "GEN"
        source = cleaned_base or cleaned_prefix
        candidate = source[:max_length] or cleaned_prefix[:max_length] or cleaned_prefix
        counter = 1

        while model.objects.filter(**{field: candidate}).exists():
            suffix = f"{counter:02d}"
            available = max_length - len(suffix)
            base_segment = source[:available] if available > 0 else ""
            if not base_segment:
                base_segment = cleaned_prefix[:available] if available > 0 else ""
            if base_segment:
                candidate = f"{base_segment}{suffix}"
            else:
                candidate = suffix[-max_length:]
            counter += 1

        return candidate

    def generate_unique_rut(self, base_value: str) -> str:
        combined = f"TMP{base_value}" if base_value else f"TMP{uuid.uuid4().hex}"
        rut = self.generate_unique_code(Company, combined, max_length=12, prefix="TMP", field="rut")
        if not rut:
            for _ in range(10):
                fallback = f"TMP{uuid.uuid4().hex[:9]}"
                if not Company.objects.filter(rut=fallback).exists():
                    return fallback[:12]
            raise CommandError("No se pudo generar un RUT temporal único")
        return rut

    def process_container_data(self, data: Dict[str, str], user: AbstractBaseUser) -> Dict[str, object]:
        processed: Dict[str, object] = {}

        processed["sequence_id"] = self.parse_int(data.get("sequence_id"))
        processed["container_number"] = self.clean_container_number(data.get("container_number"))
        processed["port"] = data.get("port", "")
        processed["seal_number"] = data.get("seal_number", "")
        processed["deposit_return"] = data.get("deposit_return", "")
        processed["storage_location"] = data.get("storage_location", "")
        processed["cd_location"] = data.get("cd_location", "")
        processed["additional_service"] = data.get("additional_service", "")
        processed["observation_1"] = data.get("observation_1", "")
        processed["observation_2"] = data.get("observation_2", "")
        processed["direct_service"] = data.get("direct_service", "")
        processed["cargo_description"] = data.get("cargo_description", "")

        processed["status"] = normalize_status(data.get("status"))
        processed["container_type"] = self.normalize_container_type(data.get("container_type"))
        processed["service_type"] = self.normalize_service_type(data.get("service_type"))

        processed["cargo_weight"] = self.parse_decimal(data.get("cargo_weight"))
        processed["total_weight"] = self.parse_decimal(data.get("total_weight"))
        processed["free_days"] = self.parse_int(data.get("free_days"))
        processed["overtime_2h"] = self.parse_int(data.get("overtime_2h"))
        processed["overtime_4h"] = self.parse_int(data.get("overtime_4h"))
        processed["extra_storage_days"] = self.parse_int(data.get("extra_storage_days"))
        processed["chassis_status"] = self.parse_int(data.get("chassis_status"))
        processed["calculated_days"] = self.parse_int(data.get("calculated_days"))

        processed["eta"] = self.parse_date(data.get("eta"))
        processed["release_date"] = self.parse_date(data.get("release_date"))
        processed["scheduled_date"] = self.parse_date(data.get("scheduled_date"))
        processed["cd_arrival_date"] = self.parse_date(data.get("cd_arrival_date"))
        processed["discharge_date"] = self.parse_date(data.get("discharge_date"))
        processed["return_date"] = self.parse_date(data.get("return_date"))
        processed["demurrage_date"] = self.parse_date(data.get("demurrage_date"))
        processed["last_update_date"] = self.parse_date(data.get("last_update_date"))

        processed["release_time"] = self.parse_time(data.get("release_time"))
        processed["scheduled_time"] = self.parse_time(data.get("scheduled_time"))
        processed["cd_arrival_time"] = self.parse_time(data.get("cd_arrival_time"))
        processed["discharge_time"] = self.parse_time(data.get("discharge_time"))
        processed["last_update_time"] = self.parse_time(data.get("last_update_time"))

        processed["has_eir"] = self.parse_boolean(data.get("has_eir"))

        processed["client"] = self.get_or_create_company(data.get("client_name"), user)
        processed["agency"] = self.get_or_create_agency(data.get("agency_name"), user)
        processed["shipping_line"] = self.get_or_create_shipping_line(data.get("shipping_line_name"), user)
        processed["vessel"] = self.get_or_create_vessel(data.get("vessel_name"), processed["shipping_line"], user)
        processed["terminal"] = self.get_or_create_location(data.get("terminal_name"), user)

        processed["owner_company"] = processed.get("client") or self.get_default_company(user)
        processed.setdefault("position_status", "floor")
        processed.setdefault("service_type", "INDIRECTO_DEPOSITO")

        if processed.get("terminal") and not processed.get("current_location"):
            processed["current_location"] = processed["terminal"]

        return processed

    def create_or_update_container(self, data: Dict[str, object], user: AbstractBaseUser):
        container_number = data["container_number"]
        try:
            container = Container.objects.get(container_number=container_number)
            for field, value in data.items():
                if value is not None:
                    setattr(container, field, value)
            container.updated_by = user
            container.save()
            return container, False
        except Container.DoesNotExist:
            data["created_by"] = user
            data["updated_by"] = user
            return Container.objects.create(**data), True

    def get_or_create_company(self, name: Optional[str], user: AbstractBaseUser):
        normalized_name = self.normalize_name(name)
        if not normalized_name:
            return None

        company = Company.objects.filter(name__iexact=normalized_name).first()
        if company:
            return company

        code = self.generate_unique_code(Company, normalized_name, max_length=50, prefix="COMP")
        rut = self.generate_unique_rut(normalized_name)
        email_stub = code.lower()[:30] or "comp"

        return Company.objects.create(
            name=normalized_name,
            code=code,
            rut=rut,
            email=f"{email_stub}@placeholder.local",
            phone="+56 2 0000 0000",
            address="Dirección no especificada",
            created_by=user,
            updated_by=user,
        )

    def get_or_create_vessel(self, name: Optional[str], shipping_line: Optional[ShippingLine], user: AbstractBaseUser):
        if not name:
            return None
        if not shipping_line:
            shipping_line, _ = ShippingLine.objects.get_or_create(
                name="Sin Especificar",
                defaults={
                    "code": "DEFAULT",
                    "created_by": user,
                    "updated_by": user,
                },
            )
        vessel, _ = Vessel.objects.get_or_create(
            name=name.strip(),
            defaults={
                "shipping_line": shipping_line,
                "created_by": user,
                "updated_by": user,
            },
        )
        return vessel

    def get_or_create_agency(self, name: Optional[str], user: AbstractBaseUser):
        normalized_name = self.normalize_name(name)
        if not normalized_name:
            return None

        agency = Agency.objects.filter(name__iexact=normalized_name).first()
        if agency:
            return agency

        code = self.generate_unique_code(Agency, normalized_name, max_length=20, prefix="AG")
        return Agency.objects.create(
            name=normalized_name,
            code=code,
            created_by=user,
            updated_by=user,
        )

    def get_or_create_shipping_line(self, name: Optional[str], user: AbstractBaseUser):
        normalized_name = self.normalize_name(name)
        if not normalized_name:
            return None

        shipping_line = ShippingLine.objects.filter(name__iexact=normalized_name).first()
        if shipping_line:
            return shipping_line

        code = self.generate_unique_code(ShippingLine, normalized_name, max_length=20, prefix="SHIP")
        return ShippingLine.objects.create(
            name=normalized_name,
            code=code,
            created_by=user,
            updated_by=user,
        )

    def get_or_create_location(self, name: Optional[str], user: AbstractBaseUser):
        normalized_name = self.normalize_name(name)
        if not normalized_name:
            return None

        location = Location.objects.filter(name__iexact=normalized_name).first()
        if location:
            return location

        return Location.objects.create(
            name=normalized_name,
            address=normalized_name,
            city="Santiago",
            region="Metropolitana",
            country="Chile",
            created_by=user,
            updated_by=user,
        )

    def get_default_company(self, user: AbstractBaseUser):
        company = Company.objects.order_by("id").first()
        if company:
            return company
        return Company.objects.create(
            name="DEFAULT COMPANY",
            code="DEFAULT",
            rut="DEFAULT-000",
            created_by=user,
            updated_by=user,
        )

    def get_user(self, user_id: int) -> AbstractBaseUser:
        try:
            return UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist as exc:
            raise CommandError(f"Usuario con ID {user_id} no existe") from exc

    def normalize_header(self, header: Optional[str]) -> str:
        if not header:
            return ""
        header = header.replace("\ufeff", "").replace("\n", " ").strip()
        header = header.replace("ï", "").replace("¿", "").replace("½", "")
        normalized = unicodedata.normalize("NFKD", header)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "", normalized)
        corrections = {
            "fechaliberaci": "fechaliberacion",
            "horaliberaci": "horaliberacion",
            "fechaprogramaci": "fechaprogramacion",
            "horaprogramaci": "horaprogramacion",
            "sobrestadiareginxcilco2horas": "sobrestadiaregionxciclo2horas",
            "sobrestadiaregiinxciclo2horas": "sobrestadiaregionxciclo2horas",
        }
        return corrections.get(normalized, normalized)

    def clean_container_number(self, value: Optional[str]) -> str:
        if not value:
            return ""
        return CONTAINER_NUMBER_RE.sub("", value.upper())

    def normalize_container_type(self, value: Optional[str]) -> str:
        if not value:
            return "40ft"
        cleaned = value.upper().replace(" ", "")
        return CONTAINER_TYPE_MAP.get(cleaned, "40ft")

    def normalize_service_type(self, value: Optional[str]) -> str:
        if not value:
            return "INDIRECTO_DEPOSITO"
        cleaned = value.upper().strip()
        return SERVICE_TYPE_MAP.get(cleaned, SERVICE_TYPE_MAP.get(cleaned.replace(" ", ""), "INDIRECTO_DEPOSITO"))

    def parse_date(self, value: Optional[str]):
        if not value:
            return None
        value = value.strip()
        if not value:
            return None
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def parse_time(self, value: Optional[str]):
        if not value:
            return None
        value = value.strip()
        if not value:
            return None
        for fmt in TIME_FORMATS:
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        return None

    def parse_decimal(self, value: Optional[str]):
        if not value:
            return None
        value = value.strip()
        if not value:
            return None
        cleaned = DECIMAL_CLEAN_RE.sub("", value)
        if not cleaned:
            return None
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return Decimal(cleaned)
        except Exception:
            return None

    def parse_int(self, value: Optional[str]) -> int:
        if not value:
            return 0
        value = value.strip()
        if not value:
            return 0
        try:
            return int(float(value.replace(",", ".")))
        except Exception:
            return 0

    def parse_boolean(self, value: Optional[str]) -> bool:
        if not value:
            return False
        return value.strip().lower() in BOOLEAN_TRUE_VALUES
