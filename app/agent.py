"""Point d'entrée de l'agent de collecte."""

from __future__ import annotations

import logging
import signal
import threading

from app.collector import MetricsCollectionError, collect_system_metrics
from app.config import Settings
from app.formatter import format_metrics
from app.sender import MetricsDeliveryError, send_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Événement d'arrêt : permet un arrêt propre sur SIGTERM (docker stop)
# au lieu d'attendre le SIGKILL envoyé après 10 secondes.
stop_event = threading.Event()


def _request_stop(signum: int, _frame: object) -> None:
    logger.info("Signal %s reçu, arrêt propre de l'agent.", signum)
    stop_event.set()


def run_once(settings: Settings) -> dict:
    """Exécute un cycle complet : collecte, formatage et envoi."""
    metrics = collect_system_metrics()
    payload = format_metrics(metrics)
    return send_metrics(
        endpoint=settings.metrics_endpoint,
        payload=payload,
        timeout=settings.request_timeout,
    )


def run_forever(event: threading.Event = stop_event) -> None:
    """Lance l'agent en mode temps réel jusqu'à réception d'un signal."""
    settings = Settings.from_env()
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    logger.info(
        "Agent démarré. Endpoint=%s, intervalle=%ss",
        settings.metrics_endpoint,
        settings.collection_interval,
    )

    while not event.is_set():
        try:
            result = run_once(settings)
            logger.info(
                "Métriques envoyées avec succès. HTTP=%s",
                result["status_code"],
            )
        except (
            MetricsCollectionError,
            MetricsDeliveryError,
            ValueError,
        ) as exc:
            logger.error("Cycle échoué : %s", exc)

        # wait() est interrompu immédiatement quand l'événement est levé.
        event.wait(settings.collection_interval)

    logger.info("Agent arrêté.")


if __name__ == "__main__":
    run_forever()
