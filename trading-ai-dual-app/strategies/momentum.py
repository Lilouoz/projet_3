"""
strategies/momentum.py
======================
Stratégie de momentum (suivi de tendance).

Adaptée des stratégies EMA-cross + MACD répandues dans Freqtrade : on suit
la tendance quand les moyennes mobiles s'alignent et que le MACD confirme.
Unifiée sous l'interface `Strategy`, non réinventée.
"""

from __future__ import annotations

import pandas as pd

from .base import Action, Signal, Strategy


class MomentumStrategy(Strategy):
    name = "momentum"
    default_timeframe = "5m"

    @staticmethod
    def default_params() -> dict:
        return {
            "ema_fast": 12,
            "ema_slow": 26,
            "macd_signal": 9,
            "stop_loss_pct": 0.025,
        }

    def _ema(self, series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    def generate(self, ohlcv: pd.DataFrame) -> Signal:
        p = self.params
        close = ohlcv["close"]
        if len(close) < p["ema_slow"] + p["macd_signal"] + 1:
            return Signal(Action.HOLD, 0.0, p["stop_loss_pct"], "Données insuffisantes").clamp()

        ema_fast = self._ema(close, p["ema_fast"])
        ema_slow = self._ema(close, p["ema_slow"])
        macd = ema_fast - ema_slow
        signal_line = self._ema(macd, p["macd_signal"])
        hist = macd - signal_line

        # Croisement récent (avant-dernier vs dernier point).
        cross_up = hist.iloc[-2] <= 0 < hist.iloc[-1]
        cross_down = hist.iloc[-2] >= 0 > hist.iloc[-1]
        trend_up = ema_fast.iloc[-1] > ema_slow.iloc[-1]

        # Conviction basée sur la force relative du momentum.
        strength = min(1.0, abs(hist.iloc[-1]) / (close.iloc[-1] * 0.005 + 1e-9))

        if cross_up and trend_up:
            return Signal(
                Action.BUY, 0.5 + 0.5 * strength, p["stop_loss_pct"],
                f"Momentum haussier: MACD croise à la hausse, EMA{p['ema_fast']}>EMA{p['ema_slow']}",
                meta={"macd_hist": hist.iloc[-1]},
            ).clamp()

        if cross_down and not trend_up:
            return Signal(
                Action.SELL, 0.5 + 0.5 * strength, p["stop_loss_pct"],
                f"Momentum baissier: MACD croise à la baisse, EMA{p['ema_fast']}<EMA{p['ema_slow']}",
                meta={"macd_hist": hist.iloc[-1]},
            ).clamp()

        return Signal(Action.HOLD, 0.0, p["stop_loss_pct"], "Pas de croisement net").clamp()
