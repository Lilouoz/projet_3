"""
dashboard/app.py
================
Tableau de bord FastAPI — pilotage EN LIVE des deux applications.

Fonctions :
  - Modifier les paramètres sans redémarrage (paires actives, taille de
    position, seuil de conviction, spread min, on/off par app et par exchange).
  - Confirmer explicitement le passage en live (règle non négociable n°1 :
    LIVE_TRADING=true dans .env NE SUFFIT PAS, il faut confirmer ici).
  - Visualiser l'état des positions, le P&L temps réel et l'historique des
    trades (lu depuis le CSV du logger).
  - Valider/rejeter les propositions manuelles de l'app-swing.

Toutes les modifications passent par `core.settings.update(...)`, thread-safe
et immédiatement pris en compte par les boucles des applications.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import EXCHANGES, get_logger, portfolio, registry, risk_manager, settings
from core.logger import TRADES_CSV

logger = get_logger("dashboard")

app = FastAPI(title="Trading AI Dual App — Dashboard", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Schémas Pydantic pour les requêtes de mise à jour
# ---------------------------------------------------------------------------
class SettingsUpdate(BaseModel):
    """Champs modifiables en live depuis le dashboard (tous optionnels)."""

    active_pairs: List[str] | None = None
    position_size_usd: float | None = None
    conviction_threshold: float | None = None
    min_spread: float | None = None
    scalp_enabled: bool | None = None
    swing_enabled: bool | None = None
    # ---- Money management (modifiable par l'utilisatrice elle-même) ----
    risk_per_trade: float | None = None        # % du capital risqué par trade
    max_daily_drawdown: float | None = None    # seuil du kill-switch journalier
    starting_capital: float | None = None      # mise de départ (base du rendement)


class ExchangeToggle(BaseModel):
    """Activation/désactivation d'un exchange en live."""

    name: str
    enabled: bool


class LiveConfirm(BaseModel):
    """Confirmation manuelle du passage en trading réel."""

    confirm: bool


# ---------------------------------------------------------------------------
# Routes API
# ---------------------------------------------------------------------------
@app.get("/api/settings")
def get_settings():
    """Retourne l'état complet des réglages (clé Claude masquée)."""
    return settings.as_dict()


@app.post("/api/settings")
def update_settings(payload: SettingsUpdate):
    """
    Met à jour un ou plusieurs paramètres EN LIVE.

    Les boucles des applications relisent ces valeurs à chaque itération,
    donc aucun redémarrage n'est nécessaire.
    """
    changes = {k: v for k, v in payload.model_dump().items() if v is not None}

    # Garde-fous de money management : on borne les valeurs sensibles pour
    # éviter une saisie dangereuse (ex. risque de 90 % par trade).
    if "risk_per_trade" in changes:
        changes["risk_per_trade"] = max(0.001, min(0.10, changes["risk_per_trade"]))
    if "max_daily_drawdown" in changes:
        changes["max_daily_drawdown"] = max(0.01, min(0.50, changes["max_daily_drawdown"]))
    if "starting_capital" in changes:
        changes["starting_capital"] = max(0.0, changes["starting_capital"])

    settings.update(**changes)

    # La mise de départ pilote aussi le calcul de rendement du portefeuille.
    if "starting_capital" in changes:
        portfolio.set_starting_capital(changes["starting_capital"])

    logger.info("Paramètres mis à jour via dashboard: %s", changes)
    return {"ok": True, "settings": settings.as_dict()}


@app.post("/api/exchange/toggle")
def toggle_exchange(payload: ExchangeToggle):
    """Active ou désactive un exchange (togglable sans restart)."""
    cfg = EXCHANGES.get(payload.name)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Exchange inconnu: {payload.name}")
    cfg.enabled = payload.enabled
    logger.info("Exchange %s -> enabled=%s", payload.name, payload.enabled)
    return {"ok": True, "exchange": payload.name, "enabled": cfg.enabled}


@app.get("/api/exchanges")
def list_exchanges():
    """État de tous les exchanges (activé, credentials, frais utilisés)."""
    out = []
    for name, cfg in EXCHANGES.items():
        conn = registry.get(name)
        out.append({
            "name": name,
            "enabled": cfg.enabled,
            "has_credentials": cfg.has_credentials,
            # Frais taker effectivement appliqués au calcul du P&L net.
            "taker_fee": conn.fee_rate if conn else None,
            # Vrai si le frais vient de TON compte (.env), pas d'un défaut.
            "fee_from_account": bool(cfg.taker_fee and cfg.taker_fee > 0),
        })
    return out


@app.post("/api/exchange/refresh-fees")
def refresh_fees(payload: ExchangeToggle):
    """
    Récupère les frais réels de ton compte via CCXT (nécessite les clés API).

    Best-effort : renvoie le frais taker réel si la plateforme l'expose.
    (On réutilise le schéma ExchangeToggle ; seul `name` est utilisé.)
    """
    conn = registry.get(payload.name)
    if conn is None:
        raise HTTPException(status_code=404, detail=f"Exchange inconnu: {payload.name}")
    taker = conn.refresh_real_fees()
    return {
        "ok": taker is not None,
        "exchange": payload.name,
        "taker_fee": conn.fee_rate,
        "note": "frais réels récupérés" if taker is not None
                else "indisponible (clés requises ou non exposé) — valeur par défaut conservée",
    }


@app.post("/api/live/confirm")
def confirm_live(payload: LiveConfirm):
    """
    Confirme (ou annule) le passage en trading réel.

    Double verrou (règle n°1) : n'a d'effet que si LIVE_TRADING=true dans
    .env. Sinon la confirmation est refusée pour rester en paper.
    """
    if payload.confirm and not settings.live_trading:
        raise HTTPException(
            status_code=400,
            detail="LIVE_TRADING=true est requis dans .env avant de confirmer le live.",
        )
    settings.update(live_confirmed=payload.confirm)
    logger.warning("Confirmation live = %s (live_trading=%s)", payload.confirm, settings.live_trading)
    return {
        "ok": True,
        "live_confirmed": settings.live_confirmed,
        "can_trade_live": settings.can_trade_live(),
    }


@app.post("/api/kill-switch/reset")
def reset_kill_switch():
    """Réarme manuellement le trading après un kill-switch (prudence !)."""
    settings.update(kill_switch=False)
    logger.warning("Kill-switch réarmé manuellement via le dashboard.")
    return {"ok": True, "kill_switch": settings.kill_switch}


@app.get("/api/status")
def status():
    """État temps réel : mode, kill-switch, drawdown, P&L."""
    return {
        "mode": "LIVE" if settings.can_trade_live() else "PAPER",
        "live_trading_env": settings.live_trading,
        "live_confirmed": settings.live_confirmed,
        "kill_switch": settings.kill_switch,
        "daily_drawdown": round(risk_manager.daily_drawdown, 4),
        "max_daily_drawdown": settings.max_daily_drawdown,
        "scalp_enabled": settings.scalp_enabled,
        "swing_enabled": settings.swing_enabled,
    }


def _price_lookup(exchange: str, symbol: str):
    """Récupère le dernier prix d'une paire pour valoriser une position."""
    conn = registry.get(exchange)
    if conn is None:
        return None
    ticker = conn.fetch_ticker(symbol)
    if not ticker:
        return None
    # 'last' est le dernier prix traité ; repli sur close si absent.
    return ticker.get("last") or ticker.get("close")


@app.get("/api/positions")
def positions():
    """
    État des positions ouvertes + performance réelle.

    Pour chaque position : P&L brut, frais, P&L net (gain réel), rendement.
    Synthèse globale rapportée à la mise de départ (rendement en %).
    """
    return portfolio.snapshot(_price_lookup)


@app.get("/api/trades")
def trades(limit: int = 50):
    """Historique des derniers trades (lu depuis le CSV du logger)."""
    if not TRADES_CSV.exists():
        return {"trades": []}
    with TRADES_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {"trades": rows[-limit:][::-1]}  # les plus récents d'abord


@app.get("/api/proposals")
def proposals():
    """
    Propositions de l'app-swing en attente de validation manuelle.

    Import paresseux pour éviter un couplage fort si l'app-swing n'est pas
    chargée dans le même process.
    """
    try:
        from importlib import import_module
        swing = import_module("main")  # app-swing/main.py sur le PYTHONPATH
        items = getattr(swing, "pending_proposals", [])
        return {
            "proposals": [
                {
                    "created_at": p.created_at,
                    "exchange": p.exchange,
                    "symbol": p.symbol,
                    "action": p.analysis.action.value,
                    "conviction": p.analysis.conviction,
                    "reasoning": p.analysis.reasoning,
                    "entry_price": p.entry_price,
                }
                for p in list(items)
            ]
        }
    except Exception:  # noqa: BLE001 — l'app-swing peut tourner ailleurs
        return {"proposals": [], "note": "app-swing non chargée dans ce process"}


@app.get("/", response_class=HTMLResponse)
def index():
    """Sert la page HTML du dashboard."""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard</h1><p>index.html manquant.</p>")


# Montage des fichiers statiques (CSS/JS additionnels éventuels).
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
