"""
core/decision.py
================
Moteur de décision DÉTERMINISTE — le garde-fou fondateur.

PRINCIPE NON NÉGOCIABLE : le LLM analyse, il n'exécute JAMAIS. Aucun ordre
ne peut être placé sur la seule sortie d'un LLM. Toute exécution passe par
ce moteur de règles qui valide, de façon reproductible :

  1. Kill-switch inactif (règle n°3).
  2. Signal cohérent : conviction ≥ seuil ET confirmation technique.
  3. Sizing valide via Kelly fractionnaire (core/sizing).
  4. Stop-loss présent (règle n°4).
  5. Exposition totale sous le plafond (somme des positions ouvertes).
  6. Rentabilité nette positive après frais (fee-aware).

Le moteur renvoie une `Decision` explicite (approuvée ou non, avec motifs)
et, si approuvée, un `OrderPlan` prêt à exécuter. Les applications ne
construisent JAMAIS un ordre en dehors de ce moteur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .config import settings
from .logger import get_logger
from .portfolio import portfolio
from .profitability import check_profitability
from .risk import OrderPlan, RiskViolation
from .sizing import size_position, stats_store

logger = get_logger("decision")


@dataclass
class TradeContext:
    """
    Contexte complet d'un trade candidat, fourni au moteur de décision.

    C'est la seule entrée du moteur : il ne consulte rien d'autre que ce
    contexte + les réglages + l'état du portefeuille.
    """

    symbol: str
    side: str                      # 'buy' ou 'sell'
    entry_price: float
    equity: float
    stop_loss_pct: float
    strategy: str                  # nom de la stratégie (pour les stats Kelly)
    conviction: float              # dans [0, 1] (LLM ramené à cette échelle)
    technical_confirmation: bool   # confirmation par indicateur déterministe
    expected_gross_return: float   # gain brut attendu (fee-aware)
    fee_rate: float                # frais taker de la plateforme
    source: str = "strategy"       # 'llm', 'whale', 'scalp', 'strategy'


@dataclass
class Decision:
    """Verdict du moteur de décision."""

    approved: bool
    plan: Optional[OrderPlan] = None
    reasons: List[str] = field(default_factory=list)

    def add(self, msg: str) -> None:
        self.reasons.append(msg)


class DecisionEngine:
    """Moteur de règles déterministe. Sans état (lit settings + portfolio)."""

    def evaluate(self, ctx: TradeContext) -> Decision:
        """
        Valide un trade candidat. N'exécute rien : renvoie un verdict + plan.

        Toutes les vérifications sont indépendantes du LLM. Un échec sur
        n'importe quelle règle => trade refusé.
        """
        decision = Decision(approved=False)

        # --- Règle 1 : kill-switch ------------------------------------
        if settings.kill_switch:
            decision.add("Kill-switch actif : aucun ordre autorisé.")
            return decision

        # --- Règle 2 : cohérence du signal ----------------------------
        if ctx.conviction < settings.conviction_threshold:
            decision.add(
                f"Conviction {ctx.conviction:.2f} < seuil {settings.conviction_threshold:.2f}."
            )
            return decision
        if not ctx.technical_confirmation:
            decision.add("Confirmation technique absente : signal non corroboré.")
            return decision

        # --- Règle 4 : stop-loss obligatoire --------------------------
        if ctx.stop_loss_pct <= 0:
            decision.add("Stop-loss manquant (règle n°4).")
            return decision

        # --- Règle 3 (sizing) : Kelly + plafonds 6% / 2% --------------
        st = stats_store.get(ctx.strategy)
        sizing = size_position(
            equity=ctx.equity,
            entry_price=ctx.entry_price,
            stop_loss_pct=ctx.stop_loss_pct,
            win_rate=st.win_rate,
            payoff_ratio=st.payoff_ratio,
            kelly_fraction=settings.kelly_fraction,
            max_position_pct=settings.max_position_pct,
            max_risk_per_trade=settings.risk_per_trade,
            # Kelly seulement si stats backtestées fiables ; sinon repli
            # prudent basé risque (ex. scalp non backtesté).
            use_kelly=st.reliable,
        )
        if sizing.amount <= 0:
            decision.add(f"Sizing nul (pas d'edge Kelly ?) — {sizing.reason()}")
            return decision

        # --- Règle 5 : exposition totale ------------------------------
        # Somme des notionals ouverts + ce trade ≤ plafond du capital.
        snap = portfolio.snapshot(lambda ex, sym: ctx.entry_price)
        current_exposure = sum(
            abs(p["amount"]) * p["entry_price"] for p in snap["positions"]
        )
        max_exposure = ctx.equity * settings.max_total_exposure_pct
        if current_exposure + sizing.notional > max_exposure:
            decision.add(
                f"Exposition totale dépassée: {current_exposure + sizing.notional:.0f} "
                f"> plafond {max_exposure:.0f}$."
            )
            return decision

        # --- Règle 6 : rentabilité nette après frais ------------------
        prof = check_profitability(
            ctx.expected_gross_return, ctx.fee_rate, settings.min_net_margin
        )
        if not prof.profitable:
            decision.add(prof.reason())
            return decision

        # --- Toutes les règles passent : on construit le plan ---------
        stop_loss = (
            ctx.entry_price * (1 - ctx.stop_loss_pct)
            if ctx.side == "buy"
            else ctx.entry_price * (1 + ctx.stop_loss_pct)
        )
        plan = OrderPlan(
            symbol=ctx.symbol,
            side=ctx.side,
            amount=sizing.amount,
            entry_price=ctx.entry_price,
            stop_loss=stop_loss,
            risk_usd=sizing.risk_usd,
        )
        decision.approved = True
        decision.plan = plan
        decision.add(f"APPROUVÉ ({ctx.source}). {sizing.reason()}. {prof.reason()}")
        logger.info("Décision APPROUVÉE %s %s: %s", ctx.side, ctx.symbol, sizing.reason())
        return decision


# Instance globale du moteur.
decision_engine = DecisionEngine()
