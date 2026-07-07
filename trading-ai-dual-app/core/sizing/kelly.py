"""
core/sizing/kelly.py
====================
Dimensionnement de position par le critère de Kelly fractionnaire.

Le critère de Kelly donne la fraction optimale du capital à engager en
fonction de l'espérance statistique d'une stratégie :

    f* = W − (1 − W) / R

où W = win rate (taux de réussite) et R = ratio gain/perte moyen
(avg_win / avg_loss). On applique une FRACTION de Kelly (half-Kelly = 0.5
par défaut) car le Kelly plein est très agressif et sensible aux erreurs
d'estimation.

Contraintes dures superposées (la plus prudente l'emporte) :
  - Plafond de 6 % du capital par position (`max_position_pct`).
  - Risque RÉEL de 2 % max par trade, calculé sur la distance au stop-loss
    (`max_risk_per_trade`).

Les paramètres W et R de chaque stratégie proviennent du backtest
(voir backtest/ + core/sizing/stats.py) et sont modifiables en live.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SizingResult:
    """Résultat détaillé du dimensionnement d'une position."""

    amount: float             # quantité en unités de l'actif de base
    notional: float           # valeur de la position en devise de cotation
    kelly_full: float         # fraction de Kelly pleine (avant fraction)
    kelly_used: float         # fraction effectivement retenue (après fraction)
    capped_by: str            # quelle contrainte a été mordante
    risk_usd: float           # montant réellement risqué jusqu'au stop

    def reason(self) -> str:
        """Explication lisible du calcul (loggée / dashboard)."""
        return (
            f"Kelly plein {self.kelly_full:.3f} → retenu {self.kelly_used:.3f} ; "
            f"notional {self.notional:.2f} ; risque {self.risk_usd:.2f}$ ; "
            f"plafonné par: {self.capped_by}"
        )


def kelly_fraction_full(win_rate: float, payoff_ratio: float) -> float:
    """
    Calcule la fraction de Kelly pleine f* = W − (1−W)/R.

    Args:
        win_rate: taux de réussite W dans [0, 1].
        payoff_ratio: ratio gain/perte moyen R (> 0).

    Returns:
        f* bornée à [0, 1]. 0 si la stratégie n'a pas d'edge positif.
    """
    if payoff_ratio <= 0:
        return 0.0
    w = max(0.0, min(1.0, win_rate))
    f = w - (1.0 - w) / payoff_ratio
    return max(0.0, min(1.0, f))


def size_position(
    equity: float,
    entry_price: float,
    stop_loss_pct: float,
    win_rate: float,
    payoff_ratio: float,
    kelly_fraction: float,
    max_position_pct: float,
    max_risk_per_trade: float,
    use_kelly: bool = True,
) -> SizingResult:
    """
    Dimensionne une position en combinant Kelly et les plafonds de risque.

    Args:
        equity: capital total disponible en devise de cotation.
        entry_price: prix d'entrée estimé.
        stop_loss_pct: distance du stop en fraction du prix (ex 0.02 = 2%).
        win_rate: W de la stratégie (issu du backtest).
        payoff_ratio: R = avg_win / avg_loss de la stratégie.
        kelly_fraction: fraction de Kelly appliquée (0.5 = half-Kelly).
        max_position_pct: plafond de taille par position (ex 0.06 = 6%).
        max_risk_per_trade: risque réel max par trade (ex 0.02 = 2%).
        use_kelly: si True, dimensionne via Kelly (stats fiables). Si False
            (stratégie non backtestée, ex. scalp), repli PRUDENT basé
            uniquement sur le risque : on part du plafond 6 % puis on réduit
            selon la limite de 2 % de risque réel. Aucun edge n'est inventé.

    Returns:
        SizingResult avec la quantité finale et le détail des contraintes.
    """
    if equity <= 0 or entry_price <= 0 or stop_loss_pct <= 0:
        return SizingResult(0.0, 0.0, 0.0, 0.0, "entrées invalides", 0.0)

    # 1) Fraction de Kelly pleine puis fractionnaire (half-Kelly par défaut).
    kfull = kelly_fraction_full(win_rate, payoff_ratio)
    kused = kfull * max(0.0, kelly_fraction)

    # 2) Notional cible : Kelly si stats fiables, sinon plafond 6 % (le risque
    #    de 2 % ci-dessous le ramènera à une taille prudente).
    notional_cap = equity * max_position_pct
    if use_kelly:
        notional_kelly = equity * kused
        notional = min(notional_kelly, notional_cap)
        capped_by = "Kelly" if notional_kelly <= notional_cap else f"plafond position {max_position_pct:.0%}"
    else:
        notional = notional_cap
        capped_by = f"plafond position {max_position_pct:.0%} (repli risque, non backtesté)"

    # 3) Quantité déduite du notional.
    amount = notional / entry_price if entry_price else 0.0

    # 4) Contrainte de risque réel : la perte au stop ne doit pas dépasser
    #    2 % du capital. On réduit la quantité si nécessaire.
    risk_usd_cap = equity * max_risk_per_trade
    risk_per_unit = entry_price * stop_loss_pct  # perte par unité au stop
    amount_risk = risk_usd_cap / risk_per_unit if risk_per_unit else 0.0
    if amount_risk < amount:
        amount = amount_risk
        notional = amount * entry_price
        capped_by = f"risque réel {max_risk_per_trade:.0%}"

    # 5) Risque effectif de la position finale.
    risk_usd = amount * risk_per_unit

    return SizingResult(
        amount=amount,
        notional=notional,
        kelly_full=kfull,
        kelly_used=kused,
        capped_by=capped_by,
        risk_usd=risk_usd,
    )
