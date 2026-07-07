"""
core/whale_tracker/scoring.py
=============================
Scoring des wallets suivis.

Un wallet n'est copié que s'il reste performant. On calcule sur une fenêtre
glissante (30 jours par défaut) :
  - win rate  : part de trades gagnants
  - pnl       : profit net cumulé
  - drawdown  : pire repli de la courbe d'équité

Un wallet dont le score passe sous les seuils configurés est automatiquement
désactivé (plus de copie), jusqu'à ce qu'il repasse au-dessus.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List

from ..config import settings


@dataclass
class WalletScore:
    """Score calculé d'un wallet sur la fenêtre glissante."""

    win_rate: float
    pnl: float
    max_drawdown: float
    trades: int
    passes: bool          # True si le wallet reste au-dessus des seuils

    def reason(self) -> str:
        """Explication du verdict (affichée dans le dashboard)."""
        status = "OK" if self.passes else "DÉSACTIVÉ"
        return (
            f"{status} — winrate {self.win_rate:.0%}, PnL {self.pnl:+.2f}, "
            f"drawdown {self.max_drawdown:.0%}, {self.trades} trades"
        )


def score_from_fills(fills: List[dict]) -> WalletScore:
    """
    Calcule le score d'un wallet à partir de ses exécutions (fills).

    Args:
        fills: liste [{pnl, time, ...}] — `time` en millisecondes epoch.

    Returns:
        WalletScore, avec `passes` selon les seuils de `settings`.
    """
    # Fenêtre glissante : on ne garde que les fills récents.
    window_ms = settings.whale_score_window_days * 24 * 3600 * 1000
    now_ms = int(time.time() * 1000)
    recent = [f for f in fills if (now_ms - f.get("time", 0)) <= window_ms]

    # On ne compte que les fills qui réalisent un PnL (clôtures).
    realized = [f for f in recent if f.get("pnl", 0) != 0]
    trades = len(realized)
    if trades == 0:
        # Pas d'historique exploitable : score neutre, désactivé par prudence.
        return WalletScore(0.0, 0.0, 0.0, 0, passes=False)

    wins = [f for f in realized if f["pnl"] > 0]
    win_rate = len(wins) / trades
    pnl = sum(f["pnl"] for f in realized)

    # Drawdown : pire repli de la courbe d'équité cumulée (ordre chronologique).
    ordered = sorted(realized, key=lambda f: f.get("time", 0))
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for f in ordered:
        equity += f["pnl"]
        peak = max(peak, equity)
        if peak > 0:
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)

    passes = (
        win_rate >= settings.whale_min_winrate
        and pnl >= settings.whale_min_pnl
        and max_dd <= settings.whale_max_drawdown
    )
    return WalletScore(
        win_rate=win_rate, pnl=pnl, max_drawdown=max_dd, trades=trades, passes=passes
    )
