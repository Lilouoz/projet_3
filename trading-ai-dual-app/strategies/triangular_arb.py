"""
strategies/triangular_arb.py
============================
Détection d'arbitrage triangulaire.

Principe éprouvé : sur un même exchange, trois paires forment un cycle
(ex. BTC/USDT, ETH/BTC, ETH/USDT). Si le produit des taux dévie de 1
au-delà des frais, une opportunité d'arbitrage existe.

Cette stratégie ne suit PAS l'interface OHLCV classique (elle a besoin des
tickers de plusieurs paires simultanément). Elle expose donc une méthode
dédiée `detect` en plus d'un `generate` neutre, pour rester compatible avec
le registre tout en signalant qu'elle s'utilise différemment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from .base import Action, Signal, Strategy


@dataclass
class ArbOpportunity:
    """Opportunité d'arbitrage triangulaire détectée."""

    cycle: List[str]       # ex. ['USDT', 'BTC', 'ETH']
    edge: float            # gain net estimé (fraction, ex 0.003 = 0.3%)
    path: List[str]        # paires empruntées
    reason: str


class TriangularArbStrategy(Strategy):
    name = "triangular_arb"
    default_timeframe = "1m"

    @staticmethod
    def default_params() -> dict:
        return {
            "fee": 0.001,          # frais par transaction (0.1 %)
            "min_edge": 0.001,     # seuil de profit net minimal (0.1 %)
            "stop_loss_pct": 0.01, # stop même sur arbitrage (règle n°4)
        }

    def detect(self, tickers: Dict[str, float], cycle: List[str]) -> Optional[ArbOpportunity]:
        """
        Détecte une opportunité sur un cycle de 3 devises.

        Args:
            tickers: dict {paire: dernier prix}, ex {'BTC/USDT': 65000, ...}.
            cycle: liste de 3 devises formant le cycle, ex ['USDT','BTC','ETH'].

        Returns:
            ArbOpportunity si l'edge net dépasse le seuil, sinon None.
        """
        p = self.params
        a, b, c = cycle
        # On tente le cycle a -> b -> c -> a.
        rate_ab = self._rate(tickers, a, b)
        rate_bc = self._rate(tickers, b, c)
        rate_ca = self._rate(tickers, c, a)
        if None in (rate_ab, rate_bc, rate_ca):
            return None

        # Produit des taux, net des frais (3 transactions).
        gross = rate_ab * rate_bc * rate_ca
        net = gross * (1 - p["fee"]) ** 3
        edge = net - 1.0

        if edge >= p["min_edge"]:
            return ArbOpportunity(
                cycle=cycle,
                edge=edge,
                path=[f"{a}->{b}", f"{b}->{c}", f"{c}->{a}"],
                reason=f"Edge net {edge:.4%} sur cycle {a}->{b}->{c}->{a}",
            )
        return None

    def _rate(self, tickers: Dict[str, float], frm: str, to: str) -> Optional[float]:
        """
        Retourne le taux de conversion frm -> to depuis les tickers.

        Cherche la paire directe `to/frm` (prix = combien de frm pour 1 to,
        donc pour convertir frm en to on divise) ou inverse `frm/to`.
        """
        direct = f"{to}/{frm}"   # ex USDT->BTC utilise BTC/USDT
        inverse = f"{frm}/{to}"
        if direct in tickers and tickers[direct]:
            return 1.0 / tickers[direct]
        if inverse in tickers and tickers[inverse]:
            return float(tickers[inverse])
        return None

    def generate(self, ohlcv: pd.DataFrame) -> Signal:
        """
        Non applicable en mode OHLCV mono-paire.

        L'arbitrage triangulaire s'utilise via `detect`. On renvoie HOLD
        pour rester compatible avec le registre de stratégies.
        """
        return Signal(
            Action.HOLD, 0.0, self.params["stop_loss_pct"],
            "Arbitrage triangulaire : utiliser detect(tickers, cycle)",
        ).clamp()
