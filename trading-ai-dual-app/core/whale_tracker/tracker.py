"""
core/whale_tracker/tracker.py
=============================
Orchestrateur du copy-trading intelligent.

- Maintient la liste ÉDITABLE des wallets suivis (persistée en JSON,
  modifiable via le dashboard : ajout / suppression / on-off).
- Rafraîchit les positions (Hyperliquid + on-chain) et le score de chaque
  wallet ; désactive automatiquement ceux sous les seuils.
- Produit des signaux de copie normalisés pour l'app-swing.
- Logique de SORTIE ANTICIPÉE : ferme la position copiée dès que le wallet
  source réduit la sienne OU que le momentum se retourne (premier signal).

Le tracker NE PASSE PAS d'ordre : il fournit des signaux au moteur de
décision déterministe (principe fondateur : rien n'exécute seul).
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..logger import get_logger
from . import hyperliquid, onchain
from .scoring import WalletScore, score_from_fills

logger = get_logger("whale.tracker")

WALLETS_FILE = Path("data") / "tracked_wallets.json"


@dataclass
class TrackedWallet:
    """Un wallet suivi et son état courant."""

    address: str
    label: str = ""
    source: str = "hyperliquid"     # 'hyperliquid' ou 'onchain'
    chain: str = "ethereum"         # pour la source on-chain
    enabled: bool = True            # suivi actif (togglable dans le dashboard)
    auto_disabled: bool = False     # désactivé automatiquement (score trop bas)
    score: Optional[dict] = None    # dernier WalletScore sérialisé
    positions: List[dict] = field(default_factory=list)  # dernières positions vues

    @property
    def active(self) -> bool:
        """Copié uniquement si activé manuellement ET pas auto-désactivé."""
        return self.enabled and not self.auto_disabled


@dataclass
class CopySignal:
    """Signal de copie proposé au moteur de décision (jamais exécuté ici)."""

    wallet: str
    symbol: str
    side: str            # 'buy' ou 'sell'
    action: str          # 'open' (copier) ou 'close' (sortie anticipée)
    reason: str


class WhaleTracker:
    """Gestionnaire thread-safe des wallets suivis et du copy-trading."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._wallets: Dict[str, TrackedWallet] = {}
        # Positions copiées actuellement ouvertes : {symbol: {wallet, side, size}}.
        self._copied: Dict[str, dict] = {}
        self.load()

    # ------------------------------------------------------------------
    # Persistance + gestion de la liste (éditable via dashboard)
    # ------------------------------------------------------------------
    def load(self) -> None:
        with self._lock:
            if WALLETS_FILE.exists():
                try:
                    raw = json.loads(WALLETS_FILE.read_text(encoding="utf-8"))
                    self._wallets = {w["address"]: TrackedWallet(**w) for w in raw}
                except (json.JSONDecodeError, TypeError):
                    self._wallets = {}

    def save(self) -> None:
        with self._lock:
            WALLETS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = [w.__dict__ for w in self._wallets.values()]
            WALLETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_wallet(self, address: str, label: str = "", source: str = "hyperliquid",
                   chain: str = "ethereum") -> TrackedWallet:
        """Ajoute un wallet à suivre (appelé par le dashboard)."""
        with self._lock:
            w = TrackedWallet(address=address, label=label, source=source, chain=chain)
            self._wallets[address] = w
            self.save()
            logger.info("Wallet suivi ajouté: %s (%s)", address, source)
            return w

    def remove_wallet(self, address: str) -> bool:
        with self._lock:
            existed = self._wallets.pop(address, None) is not None
            if existed:
                self.save()
            return existed

    def set_enabled(self, address: str, enabled: bool) -> bool:
        with self._lock:
            w = self._wallets.get(address)
            if not w:
                return False
            w.enabled = enabled
            self.save()
            return True

    def list_wallets(self) -> List[dict]:
        """État de tous les wallets (pour le dashboard)."""
        with self._lock:
            return [
                {
                    "address": w.address, "label": w.label, "source": w.source,
                    "chain": w.chain, "enabled": w.enabled,
                    "auto_disabled": w.auto_disabled, "active": w.active,
                    "score": w.score, "positions": w.positions,
                }
                for w in self._wallets.values()
            ]

    # ------------------------------------------------------------------
    # Rafraîchissement des scores + positions
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """
        Met à jour positions + score de chaque wallet et applique la
        désactivation automatique sous les seuils.
        """
        with self._lock:
            wallets = list(self._wallets.values())

        for w in wallets:
            if w.source == "hyperliquid":
                positions = hyperliquid.fetch_positions(w.address)
                fills = hyperliquid.fetch_fills(w.address)
                score = score_from_fills(fills)
            else:  # on-chain : positions inférées des transferts récents
                transfers = onchain.fetch_token_transfers(w.address, w.chain)
                positions = self._infer_positions_from_transfers(transfers)
                # Scoring on-chain simplifié : pas de PnL fiable sans prix
                # historiques -> score neutre non bloquant.
                score = WalletScore(0.5, 0.0, 0.0, len(transfers), passes=True)

            with self._lock:
                w.positions = positions
                w.score = score.__dict__
                # Désactivation automatique si sous les seuils.
                w.auto_disabled = not score.passes
                if w.auto_disabled:
                    logger.info("Wallet %s auto-désactivé: %s", w.address, score.reason())
            self.save()

    @staticmethod
    def _infer_positions_from_transfers(transfers: List[dict]) -> List[dict]:
        """Infère une exposition nette par token depuis les transferts récents."""
        net: Dict[str, float] = {}
        for t in transfers:
            sign = 1 if t["direction"] == "in" else -1
            net[t["symbol"]] = net.get(t["symbol"], 0.0) + sign * t["value"]
        return [
            {"symbol": sym, "side": "buy" if amt > 0 else "sell", "size": abs(amt),
             "entry_price": 0.0}
            for sym, amt in net.items() if amt != 0
        ]

    # ------------------------------------------------------------------
    # Génération des signaux de copie + sortie anticipée
    # ------------------------------------------------------------------
    def copy_signals(self, momentum_reversed: Optional[Dict[str, bool]] = None) -> List[CopySignal]:
        """
        Produit les signaux de copie et de sortie anticipée.

        Args:
            momentum_reversed: dict {symbol: True} indiquant un retournement de
                momentum (fourni par l'app). Déclenche une sortie anticipée.

        Returns:
            Liste de CopySignal (open/close). Ces signaux passent ensuite par
            le moteur de décision déterministe avant toute exécution.
        """
        momentum_reversed = momentum_reversed or {}
        signals: List[CopySignal] = []
        with self._lock:
            active_wallets = [w for w in self._wallets.values() if w.active]
            copied = dict(self._copied)

        # 1) Ouvertures : positions des wallets actifs non encore copiées.
        wanted: Dict[str, dict] = {}
        for w in active_wallets:
            for pos in w.positions:
                sym = pos["symbol"]
                wanted[sym] = {"wallet": w.address, "side": pos["side"], "size": pos["size"]}
                if sym not in copied:
                    signals.append(CopySignal(
                        wallet=w.address, symbol=sym, side=pos["side"], action="open",
                        reason=f"Copie de {w.label or w.address}: {pos['side']} {sym}",
                    ))

        # 2) Sorties anticipées : le wallet a réduit/fermé, OU momentum retourné.
        for sym, info in copied.items():
            wallet_closed = sym not in wanted
            reversed_mom = momentum_reversed.get(sym, False)
            if wallet_closed or reversed_mom:
                cause = "wallet source a réduit/fermé" if wallet_closed else "momentum retourné"
                exit_side = "sell" if info["side"] == "buy" else "buy"
                signals.append(CopySignal(
                    wallet=info["wallet"], symbol=sym, side=exit_side, action="close",
                    reason=f"Sortie anticipée ({cause}) sur {sym}",
                ))

        return signals

    def mark_copied(self, symbol: str, wallet: str, side: str, size: float) -> None:
        """Enregistre qu'une position a été copiée (après décision favorable)."""
        with self._lock:
            self._copied[symbol] = {"wallet": wallet, "side": side, "size": size}

    def mark_closed(self, symbol: str) -> None:
        """Retire une position copiée (après clôture)."""
        with self._lock:
            self._copied.pop(symbol, None)


# Tracker global partagé.
whale_tracker = WhaleTracker()
