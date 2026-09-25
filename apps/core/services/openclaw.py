import requests
import logging
from datetime import date, datetime
from decimal import Decimal
from django.conf import settings
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _serializable(value: Any) -> Any:
    """Convierte recursivamente Decimal/datetime/modelos Django a tipos JSON-serializables.

    Garantiza que cualquier payload que se envíe a OpenClaw (un JSON POST HTTP)
    no rompa con TypeError: Object of type Decimal is not JSON serializable, ni con
    instancias de modelos Django (driver, container, etc.) que aparecerían como
    referencias rotas en el receptor. Sub-listas y sub-dicts se procesan en cascada.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        # Float para métricas/ETA; OpenClaw no necesita precisión Decimal.
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    # Modelos Django (tienen pk + __str__); usamos str() estable.
    if hasattr(value, '_meta') and hasattr(value, 'pk'):
        return str(value)
    if isinstance(value, dict):
        return {k: _serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serializable(v) for v in value]
    # Fallback conservador: cualquier objeto raro se serializa por str().
    return str(value)


class OpenClawService:
    """
    Servicio de integración con OpenClaw para notificaciones proactivas y
    toma de decisiones en canales de mensajería (Telegram, Slack, etc.)
    """

    BASE_URL = getattr(settings, 'OPENCLAW_API_URL', 'http://localhost:3000/api/v1')
    API_KEY = getattr(settings, 'OPENCLAW_API_KEY', None)
    ENABLED = getattr(settings, 'OPENCLAW_ENABLED', False)

    @classmethod
    def _send_payload(cls, endpoint: str, payload: Dict[str, Any]) -> bool:
        if not cls.ENABLED or not cls.API_KEY:
            logger.debug("OpenClaw disabled or API Key missing.")
            return False

        try:
            headers = {
                'Authorization': f'Bearer {cls.API_KEY}',
                'Content-Type': 'application/json',
            }
            response = requests.post(
                f"{cls.BASE_URL}/{endpoint}",
                json=_serializable(payload),
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error connecting to OpenClaw: {str(e)}")
            return False

    @classmethod
    def notify_anomaly(cls, programacion: Any, anomalies: List[Dict[str, Any]]):
        """Notifica anomalías críticas P0/P1 al operador"""
        if not anomalies:
            return

        top_anomaly = anomalies[0]
        severity = top_anomaly.get('severity', 'P2')

        if severity not in ['P0', 'P1']:
            return

        payload = {
            "channel": "operator_alerts",
            "priority": "high" if severity == "P0" else "medium",
            "title": f"🚨 ANOMALÍA {severity} DETECTADA",
            "message": (
                f"Contenedor: {programacion.container.container_id}\n"
                f"Cliente: {programacion.cliente}\n"
                f"Problema: {top_anomaly.get('message')}\n"
                f"Acción recomendada: {top_anomaly.get('recommended_action')}"
            ),
            "metadata": {
                "programacion_id": programacion.id,
                "container_id": programacion.container.container_id,
                "anomalies": anomalies
            },
            "actions": [
                {"label": "Revisar en Dashboard", "url": f"{settings.SITE_URL}/programacion/{programacion.id}"},
                {"label": "Confirmar", "command": f"confirm_programacion {programacion.id}"}
            ]
        }

        cls._send_payload("notifications", payload)

    @classmethod
    def request_review(cls, programacion: Any, candidate_data: Dict[str, Any]):
        """Solicita revisión de operador para clasificación AMARILLA"""
        # candidate_data trae modelos Django (driver), Decimals (scores) y otros
        # tipos no JSON; _send_payload ahora los serializa en cascada.
        payload = {
            "channel": "operator_reviews",
            "priority": "medium",
            "title": "🟡 REVISIÓN DE ASIGNACIÓN REQUERIDA",
            "message": (
                f"Asignación sugerida para {programacion.container.container_id}\n"
                f"Conductor: {candidate_data['driver'].nombre}\n"
                f"Score: {candidate_data['score']}\n"
                f"Razón: {candidate_data['reason']}"
            ),
            "actions": [
                {"label": "Aprobar", "command": f"approve_assignment {programacion.id} {candidate_data['driver'].id}"},
                {"label": "Rechazar", "command": f"reject_assignment {programacion.id}"},
                {"label": "Ver Alternativas", "command": f"list_alternatives {programacion.id}"}
            ]
        }
        cls._send_payload("notifications", payload)
