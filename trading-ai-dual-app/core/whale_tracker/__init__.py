"""
Package `core.whale_tracker` — copy-trading intelligent.

Deux sources gratuites :
  - Hyperliquid (leaderboard / positions publiques)
  - wallets on-chain configurables (Etherscan / Polygonscan + RPC)

Scoring glissant 30 jours (win rate, PnL, drawdown) avec désactivation
automatique sous les seuils, et logique de sortie anticipée.

Expose `whale_tracker`, le tracker global, et les types associés.
"""

from .tracker import whale_tracker, WhaleTracker, TrackedWallet, CopySignal
from .scoring import WalletScore, score_from_fills

__all__ = [
    "whale_tracker",
    "WhaleTracker",
    "TrackedWallet",
    "CopySignal",
    "WalletScore",
    "score_from_fills",
]
