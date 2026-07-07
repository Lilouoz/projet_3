"""
app-swing/main.py
=================
Application 2 — Swing trading (différentiel minutes-heures).

Chaîne de traitement (le LLM analyse, le moteur de règles décide) :
  1. Toutes les 5 min : OHLCV des paires actives + positions des whales.
  2. Le LLM (Claude) produit une ANALYSE structurée JSON (thèse, conviction
     0-100, invalidation, niveaux). Timeout strict 10 s : pas de réponse =
     pas de trade (règle n°6).
  3. Confirmation TECHNIQUE déterministe (stratégie momentum) : le signal
     n'est retenu que si l'indicateur corrobore l'action du LLM.
  4. Le MOTEUR DE DÉCISION déterministe valide seul (conviction ≥ seuil ET
     confirmation technique ET sizing Kelly ET stop ET exposition ET frais).
  5. Si tout passe : exécution auto. Sinon : file de validation MANUELLE
     (validable dans le dashboard). Le copy-trading des whales passe par le
     même moteur (jamais d'exécution directe).

Aucune exécution ne se fait en dehors du moteur de décision (principe
fondateur).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Deque, Optional

from core import (
    decision_engine, get_logger, registry, risk_manager, settings, TradeContext,
)
from core.whale_tracker import whale_tracker
from strategies import Action, MomentumStrategy, ohlcv_to_dataframe

from analyzer import LLMAnalysis, MarketAnalyzer

logger = get_logger("app-swing")

LOOP_INTERVAL_S = 300  # 5 minutes

# Confirmation technique déterministe, indépendante du LLM.
_tech = MomentumStrategy()


@dataclass
class PendingProposal:
    """Proposition en attente de validation manuelle (dashboard)."""

    created_at: str
    exchange: str
    symbol: str
    side: str
    conviction: float
    thesis: str
    reasons: list
    entry_price: float


pending_proposals: Deque[PendingProposal] = deque(maxlen=50)


def _pick_exchange():
    """Premier exchange activé pour l'app-swing (None si aucun)."""
    enabled = registry.enabled_connectors()
    return enabled[0] if enabled else None


def _technical_confirms(df, llm_action: str) -> bool:
    """
    Vrai si la stratégie technique corrobore l'action du LLM.

    Corroboration = le signal technique va dans le même sens (BUY/SELL) que
    l'analyse du LLM. HOLD n'est jamais confirmé (pas de trade).
    """
    if llm_action not in ("BUY", "SELL"):
        return False
    sig = _tech.generate(df)
    return sig.action.value == llm_action


def _execute_or_queue(connector, ctx: TradeContext, thesis: str) -> None:
    """Soumet un contexte au moteur de décision : exécute ou met en attente."""
    decision = decision_engine.evaluate(ctx)
    if decision.approved and decision.plan is not None:
        connector.place_order(decision.plan, app="swing", order_type="market")
        logger.info("Trade swing exécuté %s %s — %s",
                    ctx.side, ctx.symbol, "; ".join(decision.reasons))
    else:
        # Refus du moteur OU mode manuel : on met en file de validation.
        pending_proposals.append(PendingProposal(
            created_at=datetime.now(timezone.utc).isoformat(),
            exchange=connector.name, symbol=ctx.symbol, side=ctx.side,
            conviction=ctx.conviction, thesis=thesis, reasons=decision.reasons,
            entry_price=ctx.entry_price,
        ))
        logger.info("Proposition en attente (%s %s): %s",
                    ctx.side, ctx.symbol, "; ".join(decision.reasons))


def process_symbol(connector, symbol: str, analyzer: MarketAnalyzer) -> None:
    """Analyse LLM d'une paire, confirmation technique, puis décision."""
    raw = connector.fetch_ohlcv(symbol, timeframe="5m", limit=200)
    if not raw:
        return
    df = ohlcv_to_dataframe(raw)
    entry_price = float(df["close"].iloc[-1])

    # Contexte whales pour la même paire (base symbol, ex 'BTC').
    base = symbol.split("/")[0]
    whales = [
        {"wallet": w["label"] or w["address"], "positions":
            [p for p in w["positions"] if p["symbol"].upper() == base.upper()]}
        for w in whale_tracker.list_wallets() if w["active"]
    ]

    # 2) Analyse LLM (peut être None => pas de trade, règle n°6).
    analysis: Optional[LLMAnalysis] = analyzer.analyze(symbol, df, whales)
    if analysis is None:
        logger.info("[%s] Pas d'analyse LLM exploitable — aucun trade.", symbol)
        return
    logger.info("[%s] LLM: %s conviction=%.0f/100 — %s",
                symbol, analysis.action, analysis.conviction, analysis.thesis)

    if analysis.action == "HOLD":
        return

    # 3) Confirmation technique déterministe.
    tech_ok = _technical_confirms(df, analysis.action)

    # 4) Construction du contexte et décision.
    side = "buy" if analysis.action == "BUY" else "sell"
    expected_gross = analysis.stop_loss_pct * settings.reward_risk_ratio
    ctx = TradeContext(
        symbol=symbol, side=side, entry_price=entry_price,
        equity=connector.fetch_equity(),
        stop_loss_pct=analysis.stop_loss_pct, strategy="momentum",
        conviction=analysis.conviction_ratio,
        technical_confirmation=tech_ok,
        expected_gross_return=expected_gross, fee_rate=connector.fee_rate,
        source="llm",
    )
    risk_manager.update_equity(ctx.equity)
    _execute_or_queue(connector, ctx, analysis.thesis)


def process_whale_signals(connector) -> None:
    """Route les signaux de copy-trading via le moteur de décision."""
    # Momentum retourné par paire (pour la sortie anticipée).
    momentum_reversed = {}
    for symbol in list(settings.active_pairs):
        raw = connector.fetch_ohlcv(symbol, timeframe="5m", limit=60)
        if raw:
            df = ohlcv_to_dataframe(raw)
            sig = _tech.generate(df)
            base = symbol.split("/")[0].upper()
            # Retournement = signal technique opposé notable.
            momentum_reversed[base] = sig.action == Action.SELL

    for cs in whale_tracker.copy_signals(momentum_reversed):
        # Sorties anticipées : fermeture immédiate de la position copiée.
        if cs.action == "close":
            whale_tracker.mark_closed(cs.symbol)
            logger.info("Sortie anticipée copie %s: %s", cs.symbol, cs.reason)
            continue

        # Ouvertures : on route par le moteur de décision (jamais direct).
        pair = f"{cs.symbol}/USDT"
        raw = connector.fetch_ohlcv(pair, timeframe="5m", limit=100)
        if not raw:
            continue
        df = ohlcv_to_dataframe(raw)
        entry_price = float(df["close"].iloc[-1])
        tech_ok = _technical_confirms(df, cs.side.upper())
        ctx = TradeContext(
            symbol=pair, side=cs.side, entry_price=entry_price,
            equity=connector.fetch_equity(), stop_loss_pct=0.03,
            strategy="whale_follow",
            conviction=settings.conviction_threshold,  # la copie vaut le seuil
            technical_confirmation=tech_ok,
            expected_gross_return=0.03 * settings.reward_risk_ratio,
            fee_rate=connector.fee_rate, source="whale",
        )
        decision = decision_engine.evaluate(ctx)
        if decision.approved and decision.plan is not None:
            connector.place_order(decision.plan, app="swing", order_type="market")
            whale_tracker.mark_copied(cs.symbol, cs.wallet, cs.side, decision.plan.amount)
            logger.info("Copie exécutée %s %s (%s)", cs.side, pair, cs.reason)


def run() -> None:
    """Boucle principale de l'app-swing."""
    analyzer = MarketAnalyzer()
    logger.info("Démarrage app-swing (intervalle %ss, mode=%s)",
                LOOP_INTERVAL_S, "LIVE" if settings.live_trading else "PAPER")
    for conn in registry.enabled_connectors():
        conn.refresh_real_fees()

    while True:
        start = time.monotonic()
        if not settings.swing_enabled:
            logger.info("app-swing désactivée. En veille.")
        elif settings.kill_switch:
            logger.warning("Kill-switch actif : aucune analyse.")
        else:
            connector = _pick_exchange()
            if connector is None:
                logger.warning("Aucun exchange activé pour l'app-swing.")
            else:
                # Rafraîchit les scores/positions des whales puis traite tout.
                try:
                    whale_tracker.refresh()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Refresh whales échoué: %s", exc)
                for symbol in list(settings.active_pairs):
                    try:
                        process_symbol(connector, symbol, analyzer)
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("Erreur sur %s: %s", symbol, exc)
                try:
                    process_whale_signals(connector)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Erreur signaux whales: %s", exc)

        elapsed = time.monotonic() - start
        time.sleep(max(1.0, LOOP_INTERVAL_S - elapsed))


if __name__ == "__main__":
    run()
