"""
core/whale_tracker/onchain.py
=============================
Source 2 du copy-trading : wallets on-chain configurables.

Lecture des mouvements d'un wallet via :
  - une API d'explorateur gratuite (Etherscan / Polygonscan), clé optionnelle
    dans .env (ETHERSCAN_API_KEY / POLYGONSCAN_API_KEY) ;
  - un RPC public JSON-RPC pour le solde natif.

Best-effort : sans clé d'API, on utilise le mode « no-key » (rate limité) ou
on renvoie des listes vides. Le module ne bloque jamais l'application.

Note : la liste des wallets suivis est éditable dans le dashboard (voir
`tracker.py`), pas ici.
"""

from __future__ import annotations

import os
from typing import List

import requests

from ..logger import get_logger

logger = get_logger("whale.onchain")

_TIMEOUT = 8

# Explorateurs supportés : chaîne -> (base URL, variable d'env de la clé).
_EXPLORERS = {
    "ethereum": ("https://api.etherscan.io/api", "ETHERSCAN_API_KEY"),
    "polygon": ("https://api.polygonscan.com/api", "POLYGONSCAN_API_KEY"),
}

# RPC publics par défaut (surchargables via .env <CHAIN>_RPC_URL).
_DEFAULT_RPC = {
    "ethereum": "https://eth.llamarpc.com",
    "polygon": "https://polygon-rpc.com",
}


def fetch_token_transfers(address: str, chain: str = "ethereum", limit: int = 50) -> List[dict]:
    """
    Récupère les derniers transferts de tokens ERC-20 d'un wallet.

    Sert à inférer l'activité récente (achats/ventes) d'un wallet suivi.

    Returns:
        Liste normalisée : [{symbol, direction, value, token, time, hash}].
        `direction` = 'in' (réception ~ achat) ou 'out' (envoi ~ vente).
    """
    if chain not in _EXPLORERS:
        logger.info("Chaîne non supportée: %s", chain)
        return []

    base_url, key_env = _EXPLORERS[chain]
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "page": 1,
        "offset": limit,
        "sort": "desc",
    }
    api_key = os.getenv(key_env)
    if api_key:
        params["apikey"] = api_key

    try:
        resp = requests.get(base_url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.info("Explorateur %s indisponible pour %s: %s", chain, address, exc)
        return []

    if str(data.get("status")) != "1":
        # "0" = pas de résultat ou rate-limit ; on reste silencieux.
        return []

    addr_low = address.lower()
    out: List[dict] = []
    for tx in data.get("result", []):
        try:
            decimals = int(tx.get("tokenDecimal", 18) or 18)
            value = int(tx.get("value", 0)) / (10 ** decimals)
        except (ValueError, TypeError):
            value = 0.0
        out.append({
            "symbol": tx.get("tokenSymbol", "?"),
            "direction": "in" if tx.get("to", "").lower() == addr_low else "out",
            "value": value,
            "token": tx.get("contractAddress", ""),
            "time": int(tx.get("timeStamp", 0) or 0),
            "hash": tx.get("hash", ""),
        })
    return out


def fetch_native_balance(address: str, chain: str = "ethereum") -> float:
    """
    Lit le solde natif (ETH/MATIC) d'un wallet via RPC JSON-RPC public.

    Returns:
        Solde en unité native (float). 0.0 en cas d'échec.
    """
    rpc_url = os.getenv(f"{chain.upper()}_RPC_URL", _DEFAULT_RPC.get(chain, ""))
    if not rpc_url:
        return 0.0
    try:
        resp = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0", "method": "eth_getBalance",
                "params": [address, "latest"], "id": 1,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json().get("result", "0x0")
        return int(result, 16) / 1e18
    except (requests.RequestException, ValueError) as exc:
        logger.info("RPC %s indisponible pour %s: %s", chain, address, exc)
        return 0.0
