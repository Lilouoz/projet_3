"""
core/sizing/stats.py
====================
Stockage des paramètres statistiques (Kelly) par stratégie.

Chaque stratégie possède un win rate (W) et un ratio gain/perte (R) mesurés
lors du backtest 12 mois. Ces valeurs alimentent le dimensionnement Kelly.

Le backtest écrit ces stats dans `data/strategy_stats.json` ; les
applications les lisent au runtime. Les valeurs sont modifiables en live
via le dashboard.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

STATS_FILE = Path("data") / "strategy_stats.json"


@dataclass
class StrategyStats:
    """Statistiques d'une stratégie servant au sizing Kelly."""

    win_rate: float = 0.5        # W dans [0, 1]
    payoff_ratio: float = 1.0    # R = avg_win / avg_loss
    trades: int = 0              # nombre de trades du backtest (fiabilité)
    backtested: bool = False     # True si issu d'un vrai backtest 12 mois

    @property
    def reliable(self) -> bool:
        """Stats jugées fiables si backtestées avec assez de trades."""
        return self.backtested and self.trades >= 30


class StatsStore:
    """Cache thread-safe des stats de stratégie, persisté en JSON."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stats: Dict[str, StrategyStats] = {}
        self.load()

    def load(self) -> None:
        """Charge les stats depuis le fichier JSON s'il existe."""
        with self._lock:
            if STATS_FILE.exists():
                try:
                    raw = json.loads(STATS_FILE.read_text(encoding="utf-8"))
                    self._stats = {k: StrategyStats(**v) for k, v in raw.items()}
                except (json.JSONDecodeError, TypeError):
                    self._stats = {}

    def save(self) -> None:
        """Écrit les stats courantes dans le fichier JSON."""
        with self._lock:
            STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {k: asdict(v) for k, v in self._stats.items()}
            STATS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, strategy: str) -> StrategyStats:
        """
        Retourne les stats d'une stratégie.

        Par défaut (stratégie inconnue) : W=0.5, R=1.0, non fiables — ce qui
        donne une fraction de Kelly nulle et donc un sizing prudent.
        """
        with self._lock:
            return self._stats.get(strategy, StrategyStats())

    def set(self, strategy: str, stats: StrategyStats) -> None:
        """Met à jour les stats d'une stratégie et persiste."""
        with self._lock:
            self._stats[strategy] = stats
            self.save()

    def all(self) -> Dict[str, StrategyStats]:
        with self._lock:
            return dict(self._stats)


# Store global partagé.
stats_store = StatsStore()
