from dataclasses import dataclass, asdict
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from apps.programaciones.models import Programacion
from apps.drivers.models import Driver


SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@dataclass
class OperationalAnomaly:
    code: str
    severity: str
    message: str
    recommended_action: str

    def to_dict(self):
        return asdict(self)


class DelayRiskScorer:
    @classmethod
    def score(cls, programacion: Programacion, driver: Driver | None) -> float:
        risk = 0.0

        if not driver:
            risk += 0.4
        else:
            if not driver.esta_disponible:
                risk += 0.35
            if float(driver.cumplimiento_porcentaje) < 85:
                risk += 0.25
            if float(driver.ocupacion_porcentaje) > 80:
                risk += 0.20

        if programacion.container and programacion.container.fecha_demurrage:
            horas = (programacion.container.fecha_demurrage - timezone.now()).total_seconds() / 3600
            if horas < 24:
                risk += 0.20

        if programacion.urgencia_servicio == 'CRITICO':
            risk += 0.15
        elif programacion.urgencia_servicio == 'URGENTE':
            risk += 0.10

        return max(0.0, min(1.0, round(risk, 3)))


class CapacityChecker:
    @classmethod
    def has_capacity(cls, driver: Driver | None) -> bool:
        return bool(driver and driver.esta_disponible)


class ETAEstimator:
    @classmethod
    def estimate_minutes(cls, programacion: Programacion, driver: Driver | None) -> int:
        base = 60
        if programacion.cd and getattr(programacion.cd, "tiempo_promedio_descarga_min", None):
            base += int(programacion.cd.tiempo_promedio_descarga_min)
        if driver and driver.ultima_posicion_lat and driver.ultima_posicion_lng:
            base -= 10
        if programacion.urgencia_servicio == 'CRITICO':
            base += 10
        return max(20, base)


class RouteFeasibilityValidator:
    @classmethod
    def is_feasible(cls, programacion: Programacion, eta_min: int) -> bool:
        if programacion.ventana_horaria_fin:
            eta_ts = timezone.now() + timedelta(minutes=eta_min)
            return eta_ts <= programacion.ventana_horaria_fin
        return True


class AnomalyDetector:
    @classmethod
    def detect(cls, programacion: Programacion, driver: Driver | None) -> list[dict]:
        anomalies: list[OperationalAnomaly] = []
        now = timezone.now()
        delay_threshold = float(getattr(settings, "DELAY_RISK_THRESHOLD", 0.65))
        stale_minutes = int(getattr(settings, "TRACKING_STALE_MINUTES", 30))
        incident_threshold = int(getattr(settings, "CARRIER_INCIDENT_THRESHOLD", 3))

        if driver:
            conflicting = Programacion.objects.filter(
                driver=driver,
                container__estado__in=['asignado', 'en_ruta'],
            ).exclude(pk=programacion.pk).exists()
            if conflicting:
                anomalies.append(OperationalAnomaly(
                    "ANOM_OPS_001", "P0",
                    "Vehículo/conductor ya asignado a otro servicio activo.",
                    "Escalar y reasignar recurso."
                ))

            if not driver.activo:
                anomalies.append(OperationalAnomaly(
                    "ANOM_OPS_002", "P0",
                    "Conductor sin habilitación vigente (inactivo).",
                    "Bloquear despacho automático y validar habilitación."
                ))

            if float(driver.ocupacion_porcentaje) >= 95:
                anomalies.append(OperationalAnomaly(
                    "ANOM_OPS_011", "P2",
                    "Conductor con jornada extendida.",
                    "Evaluar relevo o reasignación."
                ))

            if driver.ultima_actualizacion_posicion and (
                now - driver.ultima_actualizacion_posicion
            ).total_seconds() > stale_minutes * 60 and programacion.container.estado == 'en_ruta':
                anomalies.append(OperationalAnomaly(
                    "ANOM_OPS_013", "P1",
                    f"Viaje activo sin actualización por más de {stale_minutes} minutos.",
                    "Contactar conductor y validar estado de ruta."
                ))

        if not programacion.container.vendor:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_003", "P0",
                "Carrier sin confirmación de disponibilidad.",
                "Solicitar confirmación antes de despachar."
            ))

        if programacion.container.peso_total_tons > 28:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_006", "P0",
                "Capacidad de carga insuficiente para operación estándar.",
                "Asignar recurso de mayor capacidad."
            ))

        eta_min = ETAEstimator.estimate_minutes(programacion, driver)
        if not RouteFeasibilityValidator.is_feasible(programacion, eta_min):
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_005", "P0",
                "ETA mínimo posible supera la ventana horaria requerida.",
                "Escalar y renegociar ventana o recurso."
            ))

        if not (programacion.cd and programacion.cd.lat and programacion.cd.lng and driver and driver.ultima_posicion_lat and driver.ultima_posicion_lng):
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_007", "P1",
                "Ruta sin cobertura de tracking activa.",
                "Completar datos de ubicación y tracking antes de salida."
            ))

        history_count = Programacion.objects.filter(
            cd=programacion.cd,
            container__vendor=programacion.container.vendor,
            container__estado__in=['entregado', 'descargado', 'devuelto'],
        ).exclude(pk=programacion.pk).count()
        if history_count == 0:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_008", "P1",
                "Zona sin historial operativo del carrier.",
                "Operar con revisión de operador y confianza reducida."
            ))

        delay_risk = DelayRiskScorer.score(programacion, driver)
        if delay_risk > delay_threshold:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_009", "P1",
                f"Probabilidad de atraso superior al umbral ({delay_risk:.2f}).",
                "Revisión manual obligatoria previa al despacho."
            ))

        carrier_incidents = Programacion.objects.filter(
            container__vendor=programacion.container.vendor,
            container__estado='incidente',
            created_at__gte=now - timedelta(days=14),
        ).count()
        if carrier_incidents > incident_threshold:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_010", "P1",
                "Carrier con incidentes recientes sobre umbral.",
                "Restringir despacho automático y evaluar alternativa."
            ))

        if programacion.ventana_horaria_fin and now > programacion.ventana_horaria_fin and programacion.container.estado not in ['entregado', 'descargado', 'devuelto']:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_014", "P1",
                "Entrega no confirmada fuera de ventana.",
                "Escalar a supervisor y activar protocolo de contingencia."
            ))

        active = Programacion.objects.filter(container__estado__in=['asignado', 'en_ruta']).count()
        available = Driver.objects.filter(activo=True, presente=True).count()
        if available and (active / available) > 0.9:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_015", "P2",
                "Flota al límite de capacidad operativa.",
                "Priorizar servicios críticos y planificar refuerzo."
            ))

        if driver and driver.max_entregas_dia - driver.num_entregas_dia <= 0:
            anomalies.append(OperationalAnomaly(
                "ANOM_OPS_004", "P1",
                "Vehículo/conductor con ventana de mantención operacional próxima o saturación diaria.",
                "Asignar recurso alternativo."
            ))

        # API externa de clima no integrada, se deja criterio degradado
        anomalies.append(OperationalAnomaly(
            "ANOM_OPS_012", "P2",
            "Condición adversa en ruta no verificable (sin API externa activa).",
            "Continuar con confianza reducida y monitoreo reforzado."
        ))

        anomalies.sort(key=lambda x: SEVERITY_ORDER.get(x.severity, 99))
        return [a.to_dict() for a in anomalies]
