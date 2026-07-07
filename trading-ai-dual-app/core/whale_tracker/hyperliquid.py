"""
core/whale_tracker/hyperliquid.py
=================================
Source 1 du copy-trading : leaderboard Hyperliquid (gratuit, public).

Hyperliquid expose une API `info` (POST JSON) qui renvoie les états de
compte et positions publiques des traders. On l'utilise pour lire les
positions ouvertes d'un top-trader identifié par son adresse.

Best-effort : en cas d'indisponibilité réseau, on renvoie des listes vides
(l'application continue de tourner sans copy-trading).
"""

from __future__ import annotations

from typing import List

import requests

from ..logger import get_logger

logger = get_logger("whale.hyperliquid")

# Endpoint public de l'API info Hyperliquid.
HL_INFO_URL = "https://api.hyperliquid.xyz/info"
_TIMEOUT = 8


def fetch_positions(address: str) -> List[dict]:
    """
    Récupère les positions ouvertes d'un trader Hyperliquid.

    Args:
        address: adresse publique du trader (0x…).

    Returns:
        Liste normalisée de positions : [{symbol, side, size, entry_price}].
    """
    try:
        resp = requests.post(
            HL_INFO_URL,
            json={"type": "clearinghouseState", "user": address},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.info("Hyperliquid indisponible pour %s: %s", address, exc)
        return []

    positions: List[dict] = []
    for ap in data.get("assetPositions", []):
        pos = ap.get("position", {})
        szi = float(pos.get("szi", 0) or 0)   # taille signée (+ long / - short)
        if szi == 0:
            continue
        positions.append({
            "symbol": pos.get("coin", "?"),
            "side": "buy" if szi > 0 else "sell",
            "size": abs(szi),
            "entry_price": float(pos.get("entryPx", 0) or 0),
        })
    return positions


def fetch_fills(address: str) -> List[dict]:
    """
    Récupère l'historique récent des exécutions d'un trader (pour le scoring).

    Returns:
        Liste de fills : [{symbol, side, price, size, pnl, time}].
    """
    try:
        resp = requests.post(
            HL_INFO_URL,
            json={"type": "userFills", "user": address},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        fills = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.info("Hyperliquid fills indisponibles pour %s: %s", address, exc)
        return []

    out: List[dict] = []
    for f in fills if isinstance(fills, list) else []:
        out.append({
            "symbol": f.get("coin", "?"),
            "side": f.get("side", "?"),
            "price": float(f.get("px", 0) or 0),
            "size": float(f.get("sz", 0) or 0),
            "pnl": float(f.get("closedPnl", 0) or 0),
            "time": int(f.get("time", 0) or 0),
        })
    return out
