"""
strategies/base.py
==================
Interface `Strategy` commune à toutes les stratégies.

Objectif (règle explicite) : NE PAS réinventer les stratégies, mais unifier
sous une interface unique des approches éprouvées adaptées de Freqtrade et
de repos GitHub publics (mean reversion, momentum, grid, arbitrage
triangulaire).

Chaque stratégie reçoit un DataFrame OHLCV et renvoie un `Signal`
normalisé (BUY / SELL / HOLD + score de conviction + distance de stop-loss).
Les applications (`app-swing`, `app-scalp`) et le backtest consomment ce
même contrat.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

import pandas as pd


class Action(str, Enum):
    """Action recommandée par une stratégie."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    """
    Signal normalisé renvoyé par toute stratégie.

    Attributes:
        action: BUY / SELL / HOLD.
        conviction: score de conviction dans [0, 1].
        stop_loss_pct: distance du stop-loss en fraction du prix (> 0).
            Toujours fournie : le stop-loss est obligatoire (règle n°4).
        reason: explication lisible (loggée, affichée au dashboard).
        meta: informations additionnelles (indicateurs, niveaux…).
    """

    action: Action
    conviction: float
    stop_loss_pct: float
    reason: str = ""
    meta: Dict = field(default_factory=dict)

    def clamp(self) -> "Signal":
        """Borne la conviction dans [0, 1] et garantit un stop positif."""
        self.conviction = max(0.0, min(1.0, self.conviction))
        if self.stop_loss_pct <= 0:
            self.stop_loss_pct = 0.01  # garde-fou : stop minimal de 1 %
        return self


class Strategy(ABC):
    """
    Classe de base abstraite. Toute stratégie doit implémenter `generate`.

    Les paramètres sont passés dans un dict `params` afin de rester
    modifiables en live (le dashboard peut les mettre à jour).
    """

    #: Nom lisible de la stratégie (surchargé par les sous-classes).
    name: str = "base"
    #: Timeframe par défaut recommandé pour cette stratégie.
    default_timeframe: str = "5m"

    def __init__(self, params: Dict | None = None) -> None:
        self.params: Dict = {**self.default_params(), **(params or {})}

    @staticmethod
    def default_params() -> Dict:
        """Paramètres par défaut (surchargés par chaque stratégie)."""
        return {}

    def update_params(self, **kwargs) -> None:
        """Met à jour les paramètres en live (appelé par le dashboard)."""
        self.params.update(kwargs)

    @abstractmethod
    def generate(self, ohlcv: pd.DataFrame) -> Signal:
        """
        Analyse un DataFrame OHLCV et renvoie un `Signal`.

        Le DataFrame doit contenir les colonnes :
        ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
        """
        raise NotImplementedError


def ohlcv_to_dataframe(raw: list[list]) -> pd.DataFrame:
    """
    Convertit une liste OHLCV brute (format CCXT) en DataFrame pandas.

    Format CCXT : [timestamp_ms, open, high, low, close, volume].
    """
    df = pd.DataFrame(
        raw, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df
