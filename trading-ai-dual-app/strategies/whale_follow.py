"""
strategies/whale_follow.py
==========================
Stratégie « whale-follow » : suivre les positions des traders suivis.

Adaptée du copy-trading : le signal provient des positions agrégées des
wallets actifs (via core.whale_tracker), pas d'un indicateur OHLCV. Comme
l'arbitrage triangulaire, elle expose une méthode dédiée `signal_from_whales`
et un `generate` neutre pour rester compatible avec le registre.

Elle NE PASSE PAS d'ordre : elle produit un `Signal` consommé par le moteur
de décision déterministe (principe fondateur).
"""

from __future__ import annotations

from typing import List

import pandas as pd

from .base import Action, Signal, Strategy


class WhaleFollowStrategy(Strategy):
    name = "whale_follow"
    default_timeframe = "5m"

    @staticmethod
    def default_params() -> dict:
        return {
            # Nombre minimal de wallets alignés pour émettre un signal.
            "min_wallets_agree": 1,
            "stop_loss_pct": 0.03,
        }

    def signal_from_whales(self, base_symbol: str, wallets: List[dict]) -> Signal:
        """
        Agrège les positions des wallets actifs sur un actif donné.

        Args:
            base_symbol: actif de base, ex 'BTC'.
            wallets: liste de wallets actifs (format whale_tracker.list_wallets),
                chacun avec ses `positions`.

        Returns:
            Signal BUY/SELL si assez de wallets sont alignés, sinon HOLD.
        """
        p = self.params
        longs = shorts = 0
        for w in wallets:
            for pos in w.get("positions", []):
                if pos.get("symbol", "").upper() != base_symbol.upper():
                    continue
                if pos.get("side") == "buy":
                    longs += 1
                elif pos.get("side") == "sell":
                    shorts += 1

        # Consensus directionnel des whales.
        if longs >= p["min_wallets_agree"] and longs > shorts:
            conviction = min(1.0, longs / (longs + shorts + 1e-9))
            return Signal(Action.BUY, conviction, p["stop_loss_pct"],
                          f"{longs} whale(s) long sur {base_symbol}").clamp()
        if shorts >= p["min_wallets_agree"] and shorts > longs:
            conviction = min(1.0, shorts / (longs + shorts + 1e-9))
            return Signal(Action.SELL, conviction, p["stop_loss_pct"],
                          f"{shorts} whale(s) short sur {base_symbol}").clamp()
        return Signal(Action.HOLD, 0.0, p["stop_loss_pct"], "Pas de consensus whale").clamp()

    def generate(self, ohlcv: pd.DataFrame) -> Signal:
        """Non applicable en mode OHLCV : utiliser `signal_from_whales`."""
        return Signal(Action.HOLD, 0.0, self.params["stop_loss_pct"],
                      "Whale-follow : utiliser signal_from_whales(base, wallets)").clamp()
