"""
app-scalp/main.py
=================
Application 1 — Scalping haute fréquence.

Principe :
  - Boucle asynchrone qui suit le carnet d'ordres (orderbook) via websocket
    CCXT Pro si disponible, sinon polling REST rapide en repli.
  - Détection de micro-spreads (écart bid/ask exploitable au-delà du spread
    minimal paramétrable) et de momentum court terme (déséquilibre du carnet).
  - Exécution automatique selon les paramètres, TOUJOURS via le risk
    management (sizing 2 %, stop-loss attaché, kill-switch).

Toutes les règles non négociables s'appliquent : paper par défaut,
paramètres relus en direct, stop-loss obligatoire, kill-switch global.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from core import get_logger, registry, risk_manager, settings, RiskViolation

logger = get_logger("app-scalp")

# Fréquence de rafraîchissement du carnet en mode polling REST (repli).
POLL_INTERVAL_S = 1.0


def _orderbook_signal(order_book: dict) -> tuple[str | None, float, float]:
    """
    Analyse le carnet d'ordres et renvoie (side, spread, imbalance).

    - spread : (ask - bid) / bid, l'écart relatif.
    - imbalance : déséquilibre des volumes bid vs ask sur le top du carnet,
      dans [-1, 1] (positif => pression acheteuse => momentum haussier).

    Retourne un `side` ('buy'/'sell') si une opportunité est détectée, sinon
    None. On n'entre QUE si le spread dépasse le minimum paramétrable
    (sinon les frais mangent le gain).
    """
    bids = order_book.get("bids") or []
    asks = order_book.get("asks") or []
    if not bids or not asks:
        return None, 0.0, 0.0

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    spread = (best_ask - best_bid) / best_bid if best_bid else 0.0

    # Déséquilibre sur les 5 premiers niveaux du carnet.
    bid_vol = sum(v for _, v in bids[:5])
    ask_vol = sum(v for _, v in asks[:5])
    total = bid_vol + ask_vol
    imbalance = (bid_vol - ask_vol) / total if total else 0.0

    # Spread trop faible => pas d'opportunité rentable.
    if spread < settings.min_spread:
        return None, spread, imbalance

    # Momentum court : le sens suit le déséquilibre du carnet.
    if imbalance > 0.2:
        return "buy", spread, imbalance
    if imbalance < -0.2:
        return "sell", spread, imbalance
    return None, spread, imbalance


async def _scan_symbol(connector, symbol: str) -> None:
    """Analyse une paire une fois et exécute si opportunité + conditions OK."""
    order_book = connector.fetch_order_book(symbol, limit=20)
    if not order_book:
        return

    side, spread, imbalance = _orderbook_signal(order_book)
    if side is None:
        return

    best_bid = order_book["bids"][0][0]
    best_ask = order_book["asks"][0][0]
    entry_price = best_ask if side == "buy" else best_bid

    equity = connector.fetch_equity()
    risk_manager.update_equity(equity)

    try:
        # Stop-loss serré pour le scalp (0.3 % par défaut) — toujours présent.
        plan = risk_manager.build_order_plan(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            equity=equity,
            stop_loss_pct=0.003,
        )
        connector.place_order(plan, app="scalp", order_type="limit")
        logger.info(
            "[SCALP] %s %s @ %.4f (spread=%.4f imbalance=%.2f)",
            side, symbol, entry_price, spread, imbalance,
        )
    except RiskViolation as exc:
        logger.warning("Ordre scalp refusé: %s", exc)


async def _run_async() -> None:
    """Boucle asynchrone principale de l'app-scalp."""
    logger.info("Démarrage app-scalp (mode=%s)", "LIVE" if settings.live_trading else "PAPER")

    while True:
        # Interrupteurs et paramètres relus à chaque tour (modifiables en live).
        if not settings.scalp_enabled:
            logger.info("app-scalp désactivée (scalp_enabled=false). En veille.")
            await asyncio.sleep(5)
            continue
        if settings.kill_switch:
            logger.warning("Kill-switch actif : scalp en pause.")
            await asyncio.sleep(5)
            continue

        connector = None
        enabled = registry.enabled_connectors()
        if enabled:
            connector = enabled[0]

        if connector is None:
            logger.warning("Aucun exchange activé pour l'app-scalp.")
            await asyncio.sleep(5)
            continue

        # Scan concurrent de toutes les paires actives.
        tasks = [_scan_symbol(connector, sym) for sym in list(settings.active_pairs)]
        try:
            await asyncio.gather(*tasks)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erreur dans la boucle scalp: %s", exc)

        await asyncio.sleep(POLL_INTERVAL_S)


def run() -> None:
    """Point d'entrée synchrone (lance la boucle asyncio)."""
    try:
        asyncio.run(_run_async())
    except KeyboardInterrupt:
        logger.info("Arrêt de l'app-scalp (Ctrl+C).")


if __name__ == "__main__":
    run()
