"""
core/logger.py
==============
Journalisation des trades et des événements + système d'alertes.

- Log CSV : chaque trade (ouverture/fermeture) est écrit dans un fichier CSV
  horodaté, facilement importable dans un tableur ou par le dashboard.
- Alertes : messages critiques (kill-switch, erreurs d'exécution) envoyés
  vers la console et, si configuré, vers un webhook (Discord/Telegram/Slack).
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# Répertoire des logs, créé au besoin.
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

TRADES_CSV = LOG_DIR / "trades.csv"

# En-têtes du fichier CSV des trades.
_CSV_HEADERS = [
    "timestamp",
    "app",            # 'scalp' ou 'swing'
    "exchange",
    "symbol",
    "side",           # buy / sell
    "amount",
    "price",
    "stop_loss",
    "order_type",     # market / limit
    "mode",           # paper / live
    "pnl",            # rempli à la clôture, sinon vide
    "note",
]

# ---------------------------------------------------------------------------
# Configuration du logger standard (console + fichier).
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
    ],
)


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger nommé (un par module/app)."""
    return logging.getLogger(name)


def _ensure_csv_header() -> None:
    """Crée le fichier CSV avec son en-tête s'il n'existe pas encore."""
    if not TRADES_CSV.exists():
        with TRADES_CSV.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(_CSV_HEADERS)


def log_trade(
    app: str,
    exchange: str,
    symbol: str,
    side: str,
    amount: float,
    price: float,
    stop_loss: Optional[float] = None,
    order_type: str = "market",
    mode: str = "paper",
    pnl: Optional[float] = None,
    note: str = "",
) -> None:
    """
    Enregistre un trade dans le CSV.

    Appelé à chaque ouverture ou fermeture de position par les connecteurs
    d'exchange. Le champ `pnl` n'est renseigné qu'à la clôture.
    """
    _ensure_csv_header()
    row = [
        datetime.now(timezone.utc).isoformat(),
        app,
        exchange,
        symbol,
        side,
        f"{amount:.8f}",
        f"{price:.8f}",
        "" if stop_loss is None else f"{stop_loss:.8f}",
        order_type,
        mode,
        "" if pnl is None else f"{pnl:.4f}",
        note,
    ]
    with TRADES_CSV.open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(row)


def send_alert(message: str, level: str = "WARNING") -> None:
    """
    Envoie une alerte critique.

    Toujours loggée en console. Si `ALERT_WEBHOOK_URL` est défini dans .env,
    le message est aussi poussé vers ce webhook (format compatible
    Discord/Slack : payload JSON {"content": ...}).
    """
    logger = get_logger("alerts")
    logger.log(getattr(logging, level, logging.WARNING), "ALERTE: %s", message)

    webhook = os.getenv("ALERT_WEBHOOK_URL")
    if not webhook:
        return
    try:
        requests.post(
            webhook,
            json={"content": f"[{level}] {message}"},
            timeout=5,
        )
    except requests.RequestException as exc:  # ne jamais planter sur une alerte
        logger.error("Échec d'envoi de l'alerte vers le webhook: %s", exc)
