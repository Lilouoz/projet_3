"""
app-swing/main.py
=================
Application 2 — Swing trading sur différentiel minutes-heures.

Boucle principale :
  1. Toutes les 5 minutes, récupère les données OHLCV des paires actives.
  2. Envoie chaque paire à l'analyseur Claude (momentum, divergences,
     supports/résistances) qui renvoie BUY / SELL / HOLD + conviction.
  3. Si la conviction dépasse le seuil paramétrable ET que le trading auto
     est permis : construit un plan d'ordre via le risk management
     (sizing 2 %, stop-loss obligatoire) et l'exécute.
  4. Sinon : la proposition est mise en file de validation manuelle
     (consultable et validable depuis le dashboard).

Respecte toutes les règles non négociables : paper par défaut, kill-switch,
stop-loss attaché, paramètres modifiables en live (relus à chaque itération).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Dict

from core import get_logger, registry, risk_manager, settings, RiskViolation
from strategies import Action, ohlcv_to_dataframe

from analyzer import MarketAnalyzer, ClaudeAnalysis

logger = get_logger("app-swing")

# Intervalle de la boucle (5 min = 300 s), conforme au cahier des charges.
LOOP_INTERVAL_S = 300


@dataclass
class PendingProposal:
    """Proposition de trade en attente de validation manuelle."""

    created_at: str
    exchange: str
    symbol: str
    analysis: ClaudeAnalysis
    entry_price: float


# File des propositions en attente (partagée avec le dashboard).
# Limitée pour éviter une croissance non bornée.
pending_proposals: Deque[PendingProposal] = deque(maxlen=50)


def _pick_exchange():
    """
    Choisit le premier exchange activé pour l'app-swing.

    En pratique on peut router par paire ; ici on prend le premier activé
    pour rester simple et lisible.
    """
    enabled = registry.enabled_connectors()
    if not enabled:
        return None
    return enabled[0]


def _execute(connector, symbol: str, analysis: ClaudeAnalysis, entry_price: float) -> None:
    """Construit et exécute un ordre à partir d'une analyse convaincante."""
    equity = connector.fetch_equity()
    risk_manager.update_equity(equity)  # met à jour le drawdown / kill-switch

    side = "buy" if analysis.action == Action.BUY else "sell"
    # Gain brut espéré ≈ distance du stop × ratio gain/risque (cible de
    # profit). Le risk management refuse le trade s'il n'est pas rentable
    # une fois l'aller-retour des frais déduit (fee-aware).
    expected_gross = analysis.stop_loss_pct * settings.reward_risk_ratio
    try:
        plan = risk_manager.build_order_plan(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            equity=equity,
            stop_loss_pct=analysis.stop_loss_pct,
            expected_gross_return=expected_gross,
            fee_rate=connector.fee_rate,
        )
        connector.place_order(plan, app="swing", order_type="market")
        logger.info("Trade swing exécuté %s %s (conviction %.2f)", side, symbol, analysis.conviction)
    except RiskViolation as exc:
        # Inclut le cas « gain attendu insuffisant face aux frais ».
        logger.info("Trade swing non retenu: %s", exc)


def process_symbol(connector, symbol: str, analyzer: MarketAnalyzer) -> None:
    """Analyse une paire et décide : exécution auto ou validation manuelle."""
    raw = connector.fetch_ohlcv(symbol, timeframe="5m", limit=200)
    if not raw:
        logger.warning("Pas de données OHLCV pour %s", symbol)
        return

    df = ohlcv_to_dataframe(raw)
    entry_price = float(df["close"].iloc[-1])
    analysis = analyzer.analyze(symbol, df)

    logger.info(
        "[%s] %s conviction=%.2f (source=%s) — %s",
        symbol, analysis.action.value, analysis.conviction, analysis.source, analysis.reasoning,
    )

    # HOLD : rien à faire.
    if analysis.action == Action.HOLD:
        return

    # Seuil de conviction relu à chaque itération => modifiable en live.
    # En paper comme en live, l'exécution passe par le risk management ;
    # `place_order` simule en paper et passe un ordre réel en live.
    if analysis.conviction >= settings.conviction_threshold:
        # Exécution automatique si la conviction est suffisante.
        _execute(connector, symbol, analysis, entry_price)
    else:
        # Sinon : validation manuelle via le dashboard.
        proposal = PendingProposal(
            created_at=datetime.now(timezone.utc).isoformat(),
            exchange=connector.name,
            symbol=symbol,
            analysis=analysis,
            entry_price=entry_price,
        )
        pending_proposals.append(proposal)
        logger.info(
            "Proposition en attente de validation manuelle: %s %s (conviction %.2f < seuil %.2f)",
            analysis.action.value, symbol, analysis.conviction, settings.conviction_threshold,
        )


def _refresh_fees_on_start() -> None:
    """Récupère les frais réels de chaque exchange activé au démarrage."""
    for conn in registry.enabled_connectors():
        conn.refresh_real_fees()
        logger.info("[%s] frais taker utilisés: %.4f%%", conn.name, conn.fee_rate * 100)


def run() -> None:
    """Boucle principale de l'app-swing."""
    analyzer = MarketAnalyzer()
    logger.info("Démarrage app-swing (intervalle %ss, mode=%s)",
                LOOP_INTERVAL_S, "LIVE" if settings.live_trading else "PAPER")
    _refresh_fees_on_start()

    while True:
        start = time.monotonic()

        # On respecte les interrupteurs relus en direct (modifiables en live).
        if not settings.swing_enabled:
            logger.info("app-swing désactivée (swing_enabled=false). En veille.")
        elif settings.kill_switch:
            logger.warning("Kill-switch actif : aucune analyse exécutée.")
        else:
            connector = _pick_exchange()
            if connector is None:
                logger.warning("Aucun exchange activé pour l'app-swing.")
            else:
                for symbol in list(settings.active_pairs):
                    try:
                        process_symbol(connector, symbol, analyzer)
                    except Exception as exc:  # noqa: BLE001 — ne pas casser la boucle
                        logger.exception("Erreur sur %s: %s", symbol, exc)

        # Attente jusqu'à la prochaine itération (5 min moins le temps passé).
        elapsed = time.monotonic() - start
        time.sleep(max(1.0, LOOP_INTERVAL_S - elapsed))


if __name__ == "__main__":
    run()
