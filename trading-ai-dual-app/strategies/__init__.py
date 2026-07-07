"""
Package `strategies` — stratégies unifiées sous une interface commune.

Toutes les stratégies (adaptées de Freqtrade et de repos GitHub publics,
non réinventées) partagent le contrat `Strategy` / `Signal` défini dans
`base.py`. Un registre (`STRATEGIES`) permet de les instancier par nom,
notamment depuis le dashboard et les applications.
"""

from .base import Action, Signal, Strategy, ohlcv_to_dataframe
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .grid import GridStrategy
from .triangular_arb import TriangularArbStrategy, ArbOpportunity
from .whale_follow import WhaleFollowStrategy

# Registre nom -> classe, pour instancier dynamiquement.
STRATEGIES = {
    MeanReversionStrategy.name: MeanReversionStrategy,
    MomentumStrategy.name: MomentumStrategy,
    GridStrategy.name: GridStrategy,
    TriangularArbStrategy.name: TriangularArbStrategy,
    WhaleFollowStrategy.name: WhaleFollowStrategy,
}


def get_strategy(name: str, params: dict | None = None) -> Strategy:
    """Instancie une stratégie par son nom (KeyError si inconnue)."""
    return STRATEGIES[name](params)


__all__ = [
    "Action",
    "Signal",
    "Strategy",
    "ohlcv_to_dataframe",
    "MeanReversionStrategy",
    "MomentumStrategy",
    "GridStrategy",
    "TriangularArbStrategy",
    "ArbOpportunity",
    "WhaleFollowStrategy",
    "STRATEGIES",
    "get_strategy",
]
