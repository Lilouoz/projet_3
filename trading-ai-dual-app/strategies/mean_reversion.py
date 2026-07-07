"""
strategies/mean_reversion.py
============================
Stratégie de retour à la moyenne (mean reversion).

Approche éprouvée, adaptée des stratégies Bollinger/RSI classiques de
Freqtrade et de repos publics : on achète quand le prix s'éloigne trop en
dessous de sa moyenne (survente), on vend quand il repasse au-dessus
(surachat). Non réinventée — paramètres unifiés sous l'interface `Strategy`.
"""

from __future__ import annotations

import pandas as pd

from .base import Action, Signal, Strategy


class MeanReversionStrategy(Strategy):
    name = "mean_reversion"
    default_timeframe = "5m"

    @staticmethod
    def default_params() -> dict:
        return {
            "bb_period": 20,      # période des bandes de Bollinger
            "bb_std": 2.0,        # nombre d'écarts-types
            "rsi_period": 14,     # période du RSI
            "rsi_oversold": 30,   # seuil de survente
            "rsi_overbought": 70, # seuil de surachat
            "stop_loss_pct": 0.02,
        }

    def _rsi(self, close: pd.Series, period: int) -> pd.Series:
        """Calcul standard du RSI (Wilder)."""
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
        rs = gain / loss.replace(0, 1e-9)
        return 100 - (100 / (1 + rs))

    def generate(self, ohlcv: pd.DataFrame) -> Signal:
        p = self.params
        close = ohlcv["close"]
        if len(close) < p["bb_period"] + 1:
            return Signal(Action.HOLD, 0.0, p["stop_loss_pct"], "Données insuffisantes").clamp()

        # Bandes de Bollinger.
        ma = close.rolling(p["bb_period"]).mean()
        std = close.rolling(p["bb_period"]).std()
        upper = ma + p["bb_std"] * std
        lower = ma - p["bb_std"] * std
        rsi = self._rsi(close, p["rsi_period"])

        last = close.iloc[-1]
        last_rsi = rsi.iloc[-1]
        last_lower = lower.iloc[-1]
        last_upper = upper.iloc[-1]
        last_ma = ma.iloc[-1]

        # Signal d'achat : prix sous la bande basse + RSI en survente.
        if last <= last_lower and last_rsi <= p["rsi_oversold"]:
            # Conviction proportionnelle à l'ampleur de la survente.
            conviction = min(1.0, (p["rsi_oversold"] - last_rsi) / p["rsi_oversold"] + 0.5)
            return Signal(
                Action.BUY, conviction, p["stop_loss_pct"],
                f"Survente: prix {last:.2f} < bande basse {last_lower:.2f}, RSI {last_rsi:.1f}",
                meta={"rsi": last_rsi, "ma": last_ma},
            ).clamp()

        # Signal de vente : prix au-dessus de la bande haute + RSI en surachat.
        if last >= last_upper and last_rsi >= p["rsi_overbought"]:
            conviction = min(1.0, (last_rsi - p["rsi_overbought"]) / (100 - p["rsi_overbought"]) + 0.5)
            return Signal(
                Action.SELL, conviction, p["stop_loss_pct"],
                f"Surachat: prix {last:.2f} > bande haute {last_upper:.2f}, RSI {last_rsi:.1f}",
                meta={"rsi": last_rsi, "ma": last_ma},
            ).clamp()

        return Signal(Action.HOLD, 0.0, p["stop_loss_pct"], "Dans les bandes").clamp()
