"""
Package `core.sizing` — dimensionnement de position par Kelly fractionnaire.

Expose :
  - `size_position`   : calcul de la taille (Kelly + plafonds 6% / 2%)
  - `SizingResult`    : résultat détaillé
  - `stats_store`     : stats (W, R) par stratégie, issues du backtest
  - `StrategyStats`   : structure des stats d'une stratégie
"""

from .kelly import SizingResult, kelly_fraction_full, size_position
from .stats import StrategyStats, StatsStore, stats_store

__all__ = [
    "SizingResult",
    "kelly_fraction_full",
    "size_position",
    "StrategyStats",
    "StatsStore",
    "stats_store",
]
