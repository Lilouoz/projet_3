"""
core/portfolio.py
=================
Suivi du portefeuille : positions ouvertes, P&L et performance réelle.

Objectif : permettre à l'utilisatrice de voir dans le dashboard, en clair :
  - les positions actuellement ouvertes ;
  - pour chacune : le P&L BRUT (avant frais), les FRAIS estimés, et le
    P&L NET (le gain réel, frais déduits) ;
  - la performance globale rapportée à la MISE DE DÉPART (rendement en %),
    en séparant le réalisé (positions clôturées) et le latent (positions
    encore ouvertes).

Ce module est un singleton partagé : les connecteurs d'exchange y
enregistrent chaque ouverture/clôture, le dashboard y lit l'état courant.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

# Frais taker par défaut (0,1 %). La plupart des exchanges spot sont autour
# de cette valeur ; ajustable par position à l'ouverture.
DEFAULT_TAKER_FEE = 0.001


@dataclass
class Position:
    """Une position ouverte, avec les frais déjà payés à l'entrée."""

    exchange: str
    symbol: str
    side: str              # 'buy' (long) ou 'sell' (short)
    amount: float          # quantité en unités de l'actif de base
    entry_price: float
    stop_loss: float
    app: str               # 'scalp' ou 'swing'
    fee_rate: float = DEFAULT_TAKER_FEE
    opened_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def entry_notional(self) -> float:
        """Montant engagé à l'entrée (prix * quantité)."""
        return self.entry_price * self.amount

    @property
    def entry_fee(self) -> float:
        """Frais payés à l'ouverture de la position."""
        return self.entry_notional * self.fee_rate

    def compute_pnl(self, current_price: float) -> Tuple[float, float, float]:
        """
        Calcule le P&L latent à un prix courant donné.

        Returns:
            (pnl_brut, frais_totaux, pnl_net) où :
              - pnl_brut : gain/perte avant frais ;
              - frais_totaux : frais d'entrée + frais de sortie estimés ;
              - pnl_net : le GAIN RÉEL une fois tous les frais déduits.
        """
        if self.side == "buy":
            gross = (current_price - self.entry_price) * self.amount
        else:  # short
            gross = (self.entry_price - current_price) * self.amount
        # Frais de sortie estimés si on clôturait maintenant, au prix courant.
        exit_fee = current_price * self.amount * self.fee_rate
        total_fees = self.entry_fee + exit_fee
        net = gross - total_fees
        return gross, total_fees, net


@dataclass
class ClosedTrade:
    """Une position clôturée, avec son P&L net réalisé."""

    exchange: str
    symbol: str
    side: str
    amount: float
    entry_price: float
    exit_price: float
    gross_pnl: float
    fees: float
    net_pnl: float
    closed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Portfolio:
    """
    Portefeuille global (thread-safe).

    Suit la mise de départ, les positions ouvertes et l'historique des
    positions clôturées pour produire une synthèse de performance réelle.
    """

    def __init__(self, starting_capital: float = 0.0) -> None:
        self._lock = threading.RLock()
        self._starting_capital = starting_capital
        self._positions: Dict[str, Position] = {}
        self._closed: List[ClosedTrade] = []
        self._realized_net_pnl = 0.0   # somme des P&L nets réalisés
        self._total_fees_paid = 0.0    # cumul de tous les frais payés

    # ------------------------------------------------------------------
    # Mise de départ (capital de référence pour le rendement)
    # ------------------------------------------------------------------
    def set_starting_capital(self, value: float) -> None:
        """Définit la mise de départ servant de base au calcul du rendement."""
        with self._lock:
            self._starting_capital = float(value)

    @property
    def starting_capital(self) -> float:
        with self._lock:
            return self._starting_capital

    @staticmethod
    def _key(exchange: str, symbol: str) -> str:
        """Clé unique d'une position (un actif par exchange à la fois)."""
        return f"{exchange}:{symbol}"

    # ------------------------------------------------------------------
    # Ouverture / clôture de positions
    # ------------------------------------------------------------------
    def open_position(
        self,
        exchange: str,
        symbol: str,
        side: str,
        amount: float,
        entry_price: float,
        stop_loss: float,
        app: str,
        fee_rate: float = DEFAULT_TAKER_FEE,
    ) -> Position:
        """Enregistre une position ouverte et comptabilise ses frais d'entrée."""
        with self._lock:
            pos = Position(
                exchange=exchange, symbol=symbol, side=side, amount=amount,
                entry_price=entry_price, stop_loss=stop_loss, app=app, fee_rate=fee_rate,
            )
            self._positions[self._key(exchange, symbol)] = pos
            self._total_fees_paid += pos.entry_fee
            return pos

    def close_position(self, exchange: str, symbol: str, exit_price: float) -> Optional[ClosedTrade]:
        """
        Clôture une position au prix de sortie fourni et enregistre le
        P&L net réalisé (frais d'entrée ET de sortie déduits).
        """
        with self._lock:
            key = self._key(exchange, symbol)
            pos = self._positions.pop(key, None)
            if pos is None:
                return None
            gross, total_fees, net = pos.compute_pnl(exit_price)
            trade = ClosedTrade(
                exchange=exchange, symbol=symbol, side=pos.side, amount=pos.amount,
                entry_price=pos.entry_price, exit_price=exit_price,
                gross_pnl=gross, fees=total_fees, net_pnl=net,
            )
            self._closed.append(trade)
            self._realized_net_pnl += net
            # On a déjà compté le frais d'entrée à l'ouverture ; on ajoute
            # ici uniquement le frais de sortie (total_fees - entry_fee).
            self._total_fees_paid += (total_fees - pos.entry_fee)
            return trade

    # ------------------------------------------------------------------
    # Synthèse de performance
    # ------------------------------------------------------------------
    def snapshot(self, price_lookup: Callable[[str, str], Optional[float]]) -> Dict:
        """
        Produit l'état complet du portefeuille pour le dashboard.

        Args:
            price_lookup: fonction (exchange, symbol) -> prix courant (ou None).
                Fournie par le dashboard qui interroge les exchanges.

        Returns:
            Un dict avec la synthèse globale et le détail par position :
              - starting_capital : mise de départ
              - realized_net_pnl : gain réel déjà encaissé (positions fermées)
              - unrealized_net_pnl : gain réel latent (positions ouvertes)
              - total_net_pnl : total réel (réalisé + latent)
              - total_gross_pnl : total avant frais
              - total_fees : frais cumulés
              - return_pct : rendement en % sur la mise de départ
              - current_equity : mise de départ + total net
              - positions : liste détaillée par position ouverte
        """
        with self._lock:
            positions_out: List[Dict] = []
            unrealized_net = 0.0
            unrealized_gross = 0.0
            unrealized_fees = 0.0

            for pos in self._positions.values():
                price = price_lookup(pos.exchange, pos.symbol)
                if price is None:
                    # Prix indisponible : on affiche la position sans P&L chiffré.
                    positions_out.append({
                        "exchange": pos.exchange, "symbol": pos.symbol, "side": pos.side,
                        "amount": pos.amount, "entry_price": pos.entry_price,
                        "current_price": None, "stop_loss": pos.stop_loss,
                        "gross_pnl": None, "fees": None, "net_pnl": None,
                        "return_pct": None, "app": pos.app,
                    })
                    continue

                gross, fees, net = pos.compute_pnl(price)
                unrealized_gross += gross
                unrealized_fees += fees
                unrealized_net += net
                # Rendement de la position rapporté au montant engagé.
                pos_return = net / pos.entry_notional if pos.entry_notional else 0.0
                positions_out.append({
                    "exchange": pos.exchange, "symbol": pos.symbol, "side": pos.side,
                    "amount": pos.amount, "entry_price": pos.entry_price,
                    "current_price": price, "stop_loss": pos.stop_loss,
                    "gross_pnl": gross, "fees": fees, "net_pnl": net,
                    "return_pct": pos_return, "app": pos.app,
                })

            total_net = self._realized_net_pnl + unrealized_net
            total_gross = sum(t.gross_pnl for t in self._closed) + unrealized_gross
            return_pct = (
                total_net / self._starting_capital if self._starting_capital else 0.0
            )
            return {
                "starting_capital": self._starting_capital,
                "realized_net_pnl": self._realized_net_pnl,
                "unrealized_net_pnl": unrealized_net,
                "unrealized_gross_pnl": unrealized_gross,
                "total_net_pnl": total_net,
                "total_gross_pnl": total_gross,
                "total_fees": self._total_fees_paid,
                "return_pct": return_pct,
                "current_equity": self._starting_capital + total_net,
                "open_count": len(self._positions),
                "closed_count": len(self._closed),
                "positions": positions_out,
            }


# Singleton global partagé par les apps et le dashboard.
# La mise de départ est fixée depuis les réglages au premier accès (voir
# core/__init__.py qui l'initialise à partir de settings.starting_capital).
portfolio = Portfolio()
