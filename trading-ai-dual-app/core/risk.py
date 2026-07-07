"""
core/risk.py
============
Module central de gestion du risque. C'est le garde-fou obligatoire par
lequel TOUT ordre doit passer avant exécution.

Fonctions clés :
  1. Position sizing à 2 % du capital par trade (règle utilisatrice).
  2. Calcul et exigence d'un stop-loss attaché à CHAQUE ordre (règle n°4).
  3. Kill-switch global si le drawdown journalier dépasse 5 % (règle n°3).
  4. Suivi du P&L journalier pour déclencher le kill-switch.

Le `RiskManager` est un singleton partagé par les deux applications afin que
le drawdown soit calculé sur l'ensemble du capital, pas app par app.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .config import settings
from .logger import get_logger, send_alert
from .profitability import check_profitability

logger = get_logger("risk")


@dataclass
class OrderPlan:
    """
    Plan d'ordre validé par le risk management, prêt à être exécuté.

    Contient TOUJOURS un stop-loss (jamais None) — sinon la validation échoue.
    """

    symbol: str
    side: str            # 'buy' ou 'sell'
    amount: float        # quantité en unités de l'actif de base
    entry_price: float   # prix d'entrée estimé
    stop_loss: float     # prix du stop-loss (obligatoire)
    risk_usd: float      # montant en $ risqué sur ce trade


class RiskViolation(Exception):
    """Levée quand un ordre viole une règle de risque non négociable."""


class RiskManager:
    """
    Gestionnaire de risque global (thread-safe).

    Maintient l'équité de départ de la journée pour calculer le drawdown,
    et déclenche le kill-switch global via `settings.kill_switch`.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._day: date = date.today()
        self._start_equity: Optional[float] = None  # équité en début de journée
        self._current_equity: Optional[float] = None
        self._realized_pnl_today: float = 0.0

    # ------------------------------------------------------------------
    # Suivi de l'équité et du drawdown journalier
    # ------------------------------------------------------------------
    def _roll_day_if_needed(self, equity: float) -> None:
        """Réinitialise les compteurs journaliers au changement de date."""
        today = date.today()
        if today != self._day or self._start_equity is None:
            self._day = today
            self._start_equity = equity
            self._realized_pnl_today = 0.0
            # Nouvelle journée : on relâche le kill-switch (réarmement manuel
            # possible si l'utilisatrice le souhaite, mais on repart propre).
            settings.update(kill_switch=False)
            logger.info("Nouvelle journée de trading. Équité de départ: %.2f", equity)

    def update_equity(self, equity: float) -> None:
        """
        Met à jour l'équité courante (appelé régulièrement par les apps).

        Vérifie immédiatement le drawdown et arme le kill-switch si besoin.
        """
        with self._lock:
            self._roll_day_if_needed(equity)
            self._current_equity = equity
            self._check_drawdown()

    def _check_drawdown(self) -> None:
        """Arme le kill-switch global si le drawdown journalier > seuil."""
        if self._start_equity is None or self._current_equity is None:
            return
        if self._start_equity <= 0:
            return
        drawdown = (self._start_equity - self._current_equity) / self._start_equity
        if drawdown >= settings.max_daily_drawdown and not settings.kill_switch:
            settings.update(kill_switch=True)
            msg = (
                f"KILL-SWITCH ACTIVÉ — drawdown journalier {drawdown:.2%} "
                f">= seuil {settings.max_daily_drawdown:.2%}. "
                "Tout trading est arrêté."
            )
            logger.critical(msg)
            send_alert(msg, level="CRITICAL")

    def register_realized_pnl(self, pnl: float) -> None:
        """Ajoute un P&L réalisé (à la clôture d'une position)."""
        with self._lock:
            self._realized_pnl_today += pnl

    @property
    def daily_drawdown(self) -> float:
        """Drawdown journalier courant (0.0 si pas de perte)."""
        with self._lock:
            if not self._start_equity or self._current_equity is None:
                return 0.0
            dd = (self._start_equity - self._current_equity) / self._start_equity
            return max(dd, 0.0)

    # ------------------------------------------------------------------
    # Position sizing + stop-loss (le cœur du garde-fou)
    # ------------------------------------------------------------------
    def build_order_plan(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        equity: float,
        stop_loss_pct: float,
        expected_gross_return: float | None = None,
        fee_rate: float | None = None,
    ) -> OrderPlan:
        """
        Construit un plan d'ordre respectant toutes les règles de risque.

        Args:
            symbol: paire tradée, ex 'BTC/USDT'.
            side: 'buy' (long) ou 'sell' (short).
            entry_price: prix d'entrée estimé.
            equity: capital total disponible en devise de cotation.
            stop_loss_pct: distance du stop en fraction du prix (ex 0.01 = 1%).
            expected_gross_return: gain brut attendu en fraction (optionnel).
                Si fourni avec `fee_rate`, le trade est refusé s'il n'est pas
                rentable une fois l'aller-retour des frais déduit (fee-aware).
            fee_rate: frais taker de la plateforme en fraction (optionnel).

        Returns:
            OrderPlan avec quantité et stop-loss calculés.

        Raises:
            RiskViolation: si une règle non négociable est enfreinte, ou si le
                trade n'est pas rentable net de frais.
        """
        with self._lock:
            # Règle n°3 : aucun nouvel ordre si le kill-switch est armé.
            if settings.kill_switch:
                raise RiskViolation("Kill-switch actif : ouverture de position interdite.")

            # Garde-fous d'entrée basiques.
            if entry_price <= 0 or equity <= 0:
                raise RiskViolation("Prix d'entrée ou équité invalide.")
            if stop_loss_pct <= 0:
                # Règle n°4 : pas de stop => pas d'ordre.
                raise RiskViolation("Stop-loss obligatoire : stop_loss_pct doit être > 0.")

            # Filtre de rentabilité fee-aware : on ne prend le trade que si le
            # gain attendu couvre les frais A/R + la marge nette minimale.
            if expected_gross_return is not None and fee_rate is not None:
                check = check_profitability(
                    expected_gross_return=expected_gross_return,
                    fee_rate=fee_rate,
                    min_margin=settings.min_net_margin,
                )
                if not check.profitable:
                    raise RiskViolation(check.reason())

            # 1) Montant risqué = 2 % du capital (paramétrable en live).
            risk_usd = equity * settings.risk_per_trade

            # 2) Position sizing basé sur la distance au stop.
            #    On risque `risk_usd` si le prix atteint le stop.
            #    risque par unité = entry_price * stop_loss_pct
            risk_per_unit = entry_price * stop_loss_pct
            amount = risk_usd / risk_per_unit

            # 3) Prix du stop-loss selon le sens.
            if side == "buy":
                stop_loss = entry_price * (1 - stop_loss_pct)
            elif side == "sell":
                stop_loss = entry_price * (1 + stop_loss_pct)
            else:
                raise RiskViolation(f"Side invalide: {side!r}")

            plan = OrderPlan(
                symbol=symbol,
                side=side,
                amount=amount,
                entry_price=entry_price,
                stop_loss=stop_loss,
                risk_usd=risk_usd,
            )

            # 4) Vérification finale : le stop est bien présent (règle n°4).
            if settings.require_stop_loss and plan.stop_loss <= 0:
                raise RiskViolation("Stop-loss calculé invalide.")

            logger.info(
                "Plan validé %s %s: amount=%.6f entry=%.4f stop=%.4f risk=%.2f$",
                side, symbol, amount, entry_price, stop_loss, risk_usd,
            )
            return plan


# Singleton global partagé par toutes les applications.
risk_manager = RiskManager()
