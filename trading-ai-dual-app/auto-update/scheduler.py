"""
auto-update/scheduler.py
========================
Planificateur simple de la veille hebdomadaire.

Boucle légère qui déclenche `run_weekly_scan()` une fois par semaine.
Pour une planification robuste en production, préférer cron ou un service
externe ; ce module fournit une option autonome sans dépendance.
"""

from __future__ import annotations

import time

from core import get_logger
from scanner import run_weekly_scan

logger = get_logger("auto-update.scheduler")

# 7 jours en secondes.
WEEK_S = 7 * 24 * 3600


def run() -> None:
    """Lance un scan immédiat puis répète chaque semaine."""
    logger.info("Planificateur de veille démarré (fréquence: hebdomadaire).")
    while True:
        try:
            run_weekly_scan()
        except Exception as exc:  # noqa: BLE001 — ne jamais interrompre la boucle
            logger.exception("Échec du scan de veille: %s", exc)
        time.sleep(WEEK_S)


if __name__ == "__main__":
    run()
