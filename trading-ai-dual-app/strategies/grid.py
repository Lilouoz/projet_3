"""
strategies/grid.py
==================
Stratégie de grille (grid trading).

Inspirée des bots grid de Pionex et des implémentations open source : on
place des ordres d'achat/vente à intervalles réguliers autour d'un prix de
référence. Ici, version signal : on émet BUY quand le prix touche un niveau
de grille inférieur, SELL sur un niveau supérieur.
"""

from __future__ import annotations

import pandas as pd

from .base import Action, Signal, Strategy


class GridStrategy(Strategy):
    name = "grid"
    default_timeframe = "5m"

    @staticmethod
    def default_params() -> dict:
        return {
            "grid_levels": 10,       # nombre de niveaux de part et d'autre
            "grid_spacing": 0.005,   # espacement entre niveaux (0.5 %)
            "ref_period": 50,        # période pour le prix de référence (moyenne)
            "stop_loss_pct": 0.03,
        }

    def generate(self, ohlcv: pd.DataFrame) -> Signal:
        p = self.params
        close = ohlcv["close"]
        if len(close) < p["ref_period"] + 1:
            return Signal(Action.HOLD, 0.0, p["stop_loss_pct"], "Données insuffisantes").clamp()

        # Prix de référence = moyenne mobile centrale de la grille.
        ref = close.rolling(p["ref_period"]).mean().iloc[-1]
        last = close.iloc[-1]

        # Écart en nombre de niveaux de grille.
        deviation = (last - ref) / ref
        level = deviation / p["grid_spacing"]

        # Sous la grille => achat ; au-dessus => vente. Plus on est loin,
        # plus la conviction est forte (dans la limite des niveaux définis).
        if level <= -1:
            conviction = min(1.0, abs(level) / p["grid_levels"])
            return Signal(
                Action.BUY, conviction, p["stop_loss_pct"],
                f"Grille: prix sous réf de {abs(level):.1f} niveaux",
                meta={"ref": ref, "level": level},
            ).clamp()

        if level >= 1:
            conviction = min(1.0, abs(level) / p["grid_levels"])
            return Signal(
                Action.SELL, conviction, p["stop_loss_pct"],
                f"Grille: prix au-dessus de la réf de {level:.1f} niveaux",
                meta={"ref": ref, "level": level},
            ).clamp()

        return Signal(Action.HOLD, 0.0, p["stop_loss_pct"], "Proche de la référence").clamp()
