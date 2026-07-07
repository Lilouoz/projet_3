"""
app-swing/analyzer.py
=====================
Analyste LLM (Claude) — PRODUIT UNE ANALYSE, N'EXÉCUTE JAMAIS.

Principe fondateur : le LLM est un analyste. Il renvoie une analyse
structurée en JSON (thèse, conviction 0-100, invalidation, niveaux
support/résistance). C'est ensuite le moteur de décision déterministe
(core/decision.py) qui décide seul d'exécuter ou non.

Règle non négociable n°6 : timeout strict de 10 s sur l'appel LLM. Pas de
réponse dans le délai = pas d'analyse exploitable = PAS DE TRADE. On ne
renvoie JAMAIS de position par défaut ni de repli qui déclencherait un ordre.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from core import get_logger, settings

logger = get_logger("app-swing.analyzer")

# Import paresseux d'anthropic : sans le SDK, l'analyse LLM est simplement
# indisponible (=> pas de trade swing, jamais de position par défaut).
try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


@dataclass
class LLMAnalysis:
    """
    Analyse structurée renvoyée par le LLM.

    N'est JAMAIS un ordre : c'est une opinion consommée par le moteur de
    décision déterministe, qui applique ses propres règles.
    """

    action: str                 # 'BUY', 'SELL' ou 'HOLD'
    conviction: float           # 0-100 (échelle native du LLM)
    thesis: str                 # thèse d'investissement résumée
    invalidation: str           # condition qui invalide la thèse
    support: Optional[float]    # niveau de support identifié
    resistance: Optional[float] # niveau de résistance identifié
    stop_loss_pct: float        # distance de stop suggérée (fraction)

    @property
    def conviction_ratio(self) -> float:
        """Conviction ramenée dans [0, 1] pour le moteur de décision."""
        return max(0.0, min(1.0, self.conviction / 100.0))


# Prompt système : cadre strictement le rôle d'analyste (pas d'exécution).
_SYSTEM_PROMPT = """Tu es un analyste de trading crypto rigoureux. Tu ne passes
JAMAIS d'ordre : tu produis une analyse qu'un moteur de règles validera.
On te fournit des données de marché (OHLCV résumé, indicateurs) et,
éventuellement, les positions de traders suivis (whales).
Analyse momentum, divergences, supports/résistances.
Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour :
{
  "action": "BUY" | "SELL" | "HOLD",
  "conviction": <entier 0-100>,
  "thesis": "<thèse concise en français>",
  "invalidation": "<ce qui invaliderait la thèse>",
  "support": <prix ou null>,
  "resistance": <prix ou null>,
  "stop_loss_pct": <fraction, ex 0.02 pour 2%>
}
En cas de doute, action=HOLD et conviction basse. stop_loss_pct toujours > 0."""


class MarketAnalyzer:
    """Appelle Claude en analyste, avec timeout strict et sans repli exécutant."""

    def __init__(self) -> None:
        self._client = None
        if anthropic and settings.anthropic_api_key:
            # Timeout strict au niveau du client (règle n°6).
            self._client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key,
                timeout=settings.llm_timeout_s,
            )

    def _build_market_summary(self, symbol: str, df: pd.DataFrame, whales: Optional[list]) -> str:
        """Construit un résumé compact des données + contexte whales."""
        close = df["close"]
        recent = df.tail(30)
        summary = {
            "symbol": symbol,
            "dernier_prix": round(float(close.iloc[-1]), 4),
            "variation_30_bougies_pct": round(float((close.iloc[-1] / close.iloc[-30] - 1) * 100), 2)
            if len(close) >= 30 else None,
            "plus_haut_recent": round(float(recent["high"].max()), 4),
            "plus_bas_recent": round(float(recent["low"].min()), 4),
            "ma20": round(float(close.rolling(20).mean().iloc[-1]), 4) if len(close) >= 20 else None,
            "ma50": round(float(close.rolling(50).mean().iloc[-1]), 4) if len(close) >= 50 else None,
            "positions_whales": whales or [],
        }
        return json.dumps(summary, ensure_ascii=False)

    def analyze(self, symbol: str, df: pd.DataFrame, whales: Optional[list] = None) -> Optional[LLMAnalysis]:
        """
        Demande une analyse au LLM. Renvoie None si l'analyse est indisponible.

        None signifie explicitement « pas d'analyse => pas de trade » (règle
        n°6). On ne fabrique jamais de signal de repli qui exécuterait.
        """
        if self._client is None:
            logger.info("Pas de client LLM (clé absente) — aucune analyse, aucun trade.")
            return None

        market = self._build_market_summary(symbol, df, whales)
        try:
            message = self._client.messages.create(
                model=settings.anthropic_model,
                max_tokens=600,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Données à analyser :\n{market}"}],
                timeout=settings.llm_timeout_s,  # timeout strict par requête
            )
            text = message.content[0].text.strip()
            data = json.loads(self._extract_json(text))
            return LLMAnalysis(
                action=str(data.get("action", "HOLD")).upper(),
                conviction=float(data.get("conviction", 0)),
                thesis=str(data.get("thesis", "")),
                invalidation=str(data.get("invalidation", "")),
                support=_opt_float(data.get("support")),
                resistance=_opt_float(data.get("resistance")),
                stop_loss_pct=max(0.001, float(data.get("stop_loss_pct", 0.02))),
            )
        except Exception as exc:  # noqa: BLE001 — timeout, réseau, parsing…
            # Règle n°6 : toute défaillance => pas de trade (jamais de défaut).
            logger.warning("Analyse LLM indisponible (%s) — aucun trade.", exc)
            return None

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extrait le premier objet JSON d'une réponse (robustesse)."""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Aucun JSON dans la réponse")
        return text[start : end + 1]


def _opt_float(value) -> Optional[float]:
    """Convertit en float ou None (niveaux support/résistance optionnels)."""
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None
