"""
core/profitability.py
=====================
Filtre de rentabilité « net-edge » — tenir compte des frais réels.

Principe : un trade n'a de sens que si le gain BRUT attendu couvre
l'aller-retour des frais (frais d'entrée + frais de sortie) ET dégage une
marge nette positive. Sinon, même un trade « gagnant » en apparence finit
négatif une fois les frais déduits.

  net_edge = rendement_brut_attendu − (2 × frais)
  trade autorisé  ⇔  net_edge ≥ marge_minimale

Ce module est volontairement sans état : de simples fonctions réutilisées
par les deux applications et par le risk management.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProfitabilityCheck:
    """Résultat détaillé d'une vérification de rentabilité."""

    expected_gross: float   # rendement brut attendu (fraction, ex 0.004 = 0.4%)
    roundtrip_fees: float   # coût aller-retour des frais (fraction)
    net_edge: float         # gain net attendu après frais (fraction)
    min_margin: float       # marge nette minimale exigée
    profitable: bool        # True si le trade est jugé rentable

    def reason(self) -> str:
        """Explication lisible (loggée / affichée au dashboard)."""
        if self.profitable:
            return (
                f"Rentable: edge net {self.net_edge:.4%} ≥ marge {self.min_margin:.4%} "
                f"(brut {self.expected_gross:.4%} − frais A/R {self.roundtrip_fees:.4%})"
            )
        return (
            f"REFUSÉ: edge net {self.net_edge:.4%} < marge {self.min_margin:.4%} "
            f"(brut {self.expected_gross:.4%} − frais A/R {self.roundtrip_fees:.4%})"
        )


def check_profitability(
    expected_gross_return: float,
    fee_rate: float,
    min_margin: float,
) -> ProfitabilityCheck:
    """
    Vérifie qu'un trade est rentable une fois les frais déduits.

    Args:
        expected_gross_return: gain brut attendu en fraction du prix
            (ex. 0.004 pour un mouvement espéré de 0,4 %). Toujours >= 0.
        fee_rate: frais taker de la plateforme en fraction (ex. 0.001).
        min_margin: marge nette minimale exigée en fraction (ex. 0.001).

    Returns:
        Un ProfitabilityCheck avec le verdict et le détail du calcul.
    """
    expected_gross = abs(expected_gross_return)
    roundtrip_fees = 2.0 * max(0.0, fee_rate)  # entrée + sortie
    net_edge = expected_gross - roundtrip_fees
    return ProfitabilityCheck(
        expected_gross=expected_gross,
        roundtrip_fees=roundtrip_fees,
        net_edge=net_edge,
        min_margin=min_margin,
        profitable=net_edge >= min_margin,
    )
