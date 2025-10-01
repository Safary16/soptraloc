from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import List

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.containers.models import Agency, Container, ShippingLine, Vessel
from apps.core.models import Company, Location
from apps.drivers.models import Driver


class Command(BaseCommand):
    help = (
        "Reduce el conjunto de contenedores a un escenario pequeño y controlado "
        "para pruebas funcionales, simulando el ciclo completo de operación."
    )

    CYCLE_TEMPLATE = [
        {
            "status": "PROGRAMADO",
            "label": "Programado",
            "current_position": "CCTI",
            "position_status": "floor",
            "needs_driver": False,
            "scheduled_offset_days": 0,
            "route_minutes": None,
        },
        {
            "status": "ASIGNADO",
            "label": "Asignado",
            "current_position": "CCTI",
            "position_status": "floor",
            "needs_driver": True,
            "scheduled_offset_days": -1,
            "route_minutes": None,
        },
        {
            "status": "EN_RUTA",
            "label": "En Ruta",
            "current_position": "EN_RUTA",
            "position_status": "chassis",
            "needs_driver": True,
            "scheduled_offset_days": -1,
            "route_minutes": 120,
        },
        {
            "status": "ARRIBADO",
            "label": "Arribado",
            "current_position": "CD_QUILICURA",
            "position_status": "floor",
            "needs_driver": True,
            "scheduled_offset_days": -2,
            "route_minutes": 150,
        },
        {
            "status": "FINALIZADO",
            "label": "Finalizado",
            "current_position": "DEPOSITO_DEVOLUCION",
            "position_status": "floor",
            "needs_driver": True,
            "scheduled_offset_days": -3,
            "route_minutes": 180,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--replicas",
            type=int,
            default=1,
            help="Cantidad de ciclos completos a generar (cada ciclo contiene 5 contenedores).",
        )
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Elimina cualquier contenedor que no forme parte del escenario generado.",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default="SIMX",
            help="Prefijo alfanumérico para los números de contenedor generados (4 caracteres).",
        )

    def handle(self, *args, **options):
        replicas = max(1, options["replicas"])
        prefix = options["prefix"].upper()[:4].ljust(4, "X")
        purge = options["purge"]

        with transaction.atomic():
            company = self._get_or_create_company()
            shipping_line = self._get_or_create_shipping_line()
            agency = self._get_or_create_agency()
            vessel = self._get_or_create_vessel(shipping_line)
            terminal = self._get_or_create_location(
                name="Terminal CCTI",
                city="Maipú",
                region="Metropolitana",
                address="Base CCTI, Maipú",
            )
            cd_location = self._get_or_create_location(
                name="CD Quilicura",
                city="Quilicura",
                region="Metropolitana",
                address="Centro de Distribución Quilicura",
            )
            deposito = self._get_or_create_location(
                name="Depósito Devolución",
                city="Pudahuel",
                region="Metropolitana",
                address="Depósito de devolución SoptraLoc",
            )

            driver_pool = self._ensure_driver_pool(replicas)
            Driver.objects.filter(contenedor_asignado__isnull=False).update(contenedor_asignado=None)

            created_numbers: List[str] = []
            now = timezone.now()
            base_date = timezone.localdate()

            self.stdout.write(self.style.NOTICE("📦 Generando contenedores de prueba..."))

            for replica_index in range(replicas):
                for template_index, template in enumerate(self.CYCLE_TEMPLATE):
                    serial = replica_index * len(self.CYCLE_TEMPLATE) + template_index + 1
                    container_number = f"{prefix}{serial:07d}"
                    sequence_id = serial

                    scheduled_date = base_date + timedelta(days=template["scheduled_offset_days"])
                    release_date = scheduled_date - timedelta(days=1)
                    arrival_date = scheduled_date + timedelta(days=1)

                    if template["status"] == "FINALIZADO":
                        current_location = deposito
                    elif template["status"] == "ARRIBADO":
                        current_location = cd_location
                    elif template["status"] in {"PROGRAMADO", "ASIGNADO"}:
                        current_location = terminal
                    else:
                        current_location = None

                    cd_location_str = "Depósito Devolución" if template["status"] == "FINALIZADO" else "CD Quilicura"

                    defaults = {
                        "sequence_id": sequence_id,
                        "status": template["status"],
                        "container_type": "40hc",
                        "service_type": "DIRECTO",
                        "owner_company": company,
                        "client": company,
                        "terminal": terminal,
                        "current_location": current_location,
                        "seal_number": f"SIM-{serial:05d}",
                        "eta": release_date,
                        "release_date": release_date,
                        "release_time": time(7, 30),
                        "scheduled_date": scheduled_date,
                        "scheduled_time": time(8, 0),
                        "cd_arrival_date": arrival_date if template["status"] in {"ARRIBADO", "FINALIZADO"} else None,
                        "cd_arrival_time": time(10, 0) if template["status"] in {"ARRIBADO", "FINALIZADO"} else None,
                        "discharge_date": arrival_date if template["status"] == "FINALIZADO" else None,
                        "discharge_time": time(11, 0) if template["status"] == "FINALIZADO" else None,
                        "return_date": arrival_date + timedelta(days=1) if template["status"] == "FINALIZADO" else None,
                        "has_eir": template["status"] == "FINALIZADO",
                        "agency": agency,
                        "shipping_line": shipping_line,
                        "vessel": vessel,
                        "cargo_description": f"Carga demo ciclo {template['label'].lower()}",
                        "cd_location": cd_location_str,
                        "current_position": template["current_position"],
                        "position_status": template["position_status"],
                        "position_updated_at": now,
                        "calculated_days": (arrival_date - release_date).days if arrival_date else 0,
                        "duracion_ruta": template["route_minutes"],
                        "duracion_total": template["route_minutes"] + 60 if template["route_minutes"] else None,
                        "observation_1": "Escenario de prueba controlado",
                        "observation_2": "Generado por setup_testing_cycle",
                    }

                    container, created = Container.objects.update_or_create(
                        container_number=container_number,
                        defaults=defaults,
                    )

                    self._apply_time_markers(container, now)

                    if template["needs_driver"]:
                        driver = driver_pool[(serial - 1) % len(driver_pool)]
                        container.conductor_asignado = driver
                        container.save(update_fields=[
                            "conductor_asignado",
                            "tiempo_asignacion",
                            "tiempo_inicio_ruta",
                            "tiempo_llegada",
                            "tiempo_descarga",
                            "tiempo_finalizacion",
                            "duracion_descarga",
                            "duracion_total",
                            "duracion_ruta",
                        ])
                        driver.contenedor_asignado = container
                        driver.estado = "OPERATIVO"
                        driver.save(update_fields=["contenedor_asignado", "estado"])
                    else:
                        container.conductor_asignado = None
                        container.save(update_fields=[
                            "conductor_asignado",
                            "tiempo_asignacion",
                            "tiempo_inicio_ruta",
                            "tiempo_llegada",
                            "tiempo_descarga",
                            "tiempo_finalizacion",
                            "duracion_descarga",
                            "duracion_total",
                            "duracion_ruta",
                        ])

                    created_numbers.append(container.container_number)

                    state_label = template["label"]
                    action = "Creado" if created else "Actualizado"
                    self.stdout.write(self.style.SUCCESS(f"  • {action} {container.container_number} → {state_label}"))

            if purge:
                removed, _ = Container.objects.exclude(container_number__in=created_numbers).delete()
                self.stdout.write(self.style.WARNING(f"🧹 Eliminados {removed} contenedores fuera del escenario"))

        self.stdout.write(self.style.SUCCESS("✅ Escenario de prueba listo"))
        self.stdout.write(self.style.SUCCESS(f"📊 Contenedores disponibles: {len(created_numbers)}"))

    def _apply_time_markers(self, container: Container, now: datetime) -> None:
        """Asignar marcas temporales coherentes según el estado actual."""
        two_hours_ago = now - timedelta(hours=2)
        ninety_minutes_ago = now - timedelta(minutes=90)
        forty_five_minutes_ago = now - timedelta(minutes=45)
        thirty_minutes_ago = now - timedelta(minutes=30)
        twenty_minutes_ago = now - timedelta(minutes=20)

        container.tiempo_asignacion = None
        container.tiempo_inicio_ruta = None
        container.tiempo_llegada = None
        container.tiempo_descarga = None
        container.tiempo_finalizacion = None
        container.duracion_descarga = None

        if container.status in {"ASIGNADO", "EN_RUTA", "ARRIBADO", "FINALIZADO"}:
            container.tiempo_asignacion = two_hours_ago
        if container.status in {"EN_RUTA", "ARRIBADO", "FINALIZADO"}:
            container.tiempo_inicio_ruta = ninety_minutes_ago
        if container.status in {"ARRIBADO", "FINALIZADO"}:
            container.tiempo_llegada = forty_five_minutes_ago
        if container.status == "FINALIZADO":
            container.tiempo_descarga = thirty_minutes_ago
            container.tiempo_finalizacion = twenty_minutes_ago
            container.duracion_descarga = 15
            container.duracion_total = container.duracion_total or 195
        container.save(update_fields=[
            "tiempo_asignacion",
            "tiempo_inicio_ruta",
            "tiempo_llegada",
            "tiempo_descarga",
            "tiempo_finalizacion",
            "duracion_descarga",
            "duracion_total",
        ])

    def _get_or_create_company(self) -> Company:
        company = Company.objects.filter(code__in=["WALMART", "WMSYS", "WAL"], is_active=True).first()
        if company:
            return company
        return Company.objects.create(
            name="Walmart Demo",
            code="WMSIM",
            rut="76.123.456-7",
            email="demo@soptraloc.com",
            phone="+56226800000",
            address="Ruta 68 KM 12, Pudahuel",
        )

    def _get_or_create_shipping_line(self) -> ShippingLine:
        shipping_line, _ = ShippingLine.objects.get_or_create(
            code="SIMLINE",
            defaults={
                "name": "Simulated Shipping Line",
                "contact_info": "demo@soptraloc.com",
            },
        )
        return shipping_line

    def _get_or_create_agency(self) -> Agency:
        agency, _ = Agency.objects.get_or_create(
            code="SIMAGY",
            defaults={
                "name": "Agencia Demo",
                "contact_info": "Agencia demo para escenarios de prueba",
            },
        )
        return agency

    def _get_or_create_vessel(self, shipping_line: ShippingLine) -> Vessel:
        vessel, _ = Vessel.objects.get_or_create(
            name="Soptra Demo Express",
            shipping_line=shipping_line,
            defaults={
                "imo_number": "SIM1234567",
            },
        )
        return vessel

    def _get_or_create_location(self, name: str, city: str, region: str, address: str) -> Location:
        location, _ = Location.objects.get_or_create(
            name=name,
            defaults={
                "city": city,
                "region": region,
                "address": address,
                "country": "Chile",
            },
        )
        return location

    def _ensure_driver_pool(self, replicas: int) -> List[Driver]:
        required = max(3, replicas * 3)
        drivers = list(Driver.objects.filter(is_active=True).order_by("nombre")[:required])

        if len(drivers) >= required:
            return drivers

        to_create = required - len(drivers)
        self.stdout.write(self.style.WARNING(f"👷 Creando {to_create} conductores demo adicionales"))

        base_index = Driver.objects.count() + 1
        for offset in range(to_create):
            Driver.objects.create(
                nombre=f"Conductor Demo {base_index + offset}",
                rut=f"99{base_index + offset:07d}-{(offset % 9)+1}",
                telefono="+56900000000",
                ppu=f"SIM{base_index + offset:03d}",
                tracto="SIM-TRACTO",
                tipo_conductor="LOCALERO",
                estado="OPERATIVO",
                coordinador="Demo",
                faena="Testing",
                ubicacion_actual="CCTI",
            )

        return list(Driver.objects.filter(is_active=True).order_by("nombre")[:required])
