"""
app-swing/analyzer.py
=====================
Analyse de marché via l'API Claude (Anthropic).

L'app-swing raisonne sur des échelles minutes-heures. Elle envoie à Claude
un résumé structuré des données OHLCV récentes + des indicateurs techniques,
et demande un signal BUY/SELL/HOLD accompagné d'un score de conviction et
d'une justification (momentum, divergences, supports/résistances).

La clé API est lue depuis `.env` (jamais en dur). Si aucune clé n'est
configurée, l'analyseur bascule sur un fallback local (stratégies techniques)
afin que l'application reste fonctionnelle en paper trading.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from core import get_logger, settings
from strategies import Action, MomentumStrategy, Signal

logger = get_logger("app-swing.analyzer")

# Import paresseux d'anthropic : l'app fonctionne même sans le SDK installé
# (fallback technique), utile en environnement minimal.
try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


@dataclass
class ClaudeAnalysis:
    """Résultat d'analyse renvoyé au moteur de l'app-swing."""

    action: Action
    conviction: float          # dans [0, 1]
    stop_loss_pct: float
    reasoning: str
    source: str                # 'claude' ou 'fallback'


# Prompt système : cadre le rôle de Claude en analyste technique prudent.
_SYSTEM_PROMPT = """Tu es un analyste de trading crypto rigoureux et prudent.
On te fournit des données de marché récentes (OHLCV) et des indicateurs.
Analyse le momentum, les divergences, et les supports/résistances.
Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format :
{
  "action": "BUY" | "SELL" | "HOLD",
  "conviction": <nombre entre 0 et 1>,
  "stop_loss_pct": <fraction du prix, ex 0.02 pour 2%>,
  "reasoning": "<explication concise en français>"
}
Rappels de gestion du risque : privilégie HOLD en cas de doute ; un
stop-loss est OBLIGATOIRE (stop_loss_pct toujours > 0)."""


class MarketAnalyzer:
    """Encapsule les appels à Claude et le fallback technique."""

    def __init__(self) -> None:
        self._client = None
        if anthropic and settings.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        # Stratégie technique utilisée en secours (pas de clé / erreur API).
        self._fallback = MomentumStrategy()

    def _build_market_summary(self, symbol: str, df: pd.DataFrame) -> str:
        """
        Construit un résumé textuel compact des données pour le prompt.

        On n'envoie pas des centaines de bougies : on résume les niveaux
        clés et quelques statistiques pour rester économe en tokens.
        """
        close = df["close"]
        recent = df.tail(30)
        summary = {
            "symbol": symbol,
            "dernier_prix": round(float(close.iloc[-1]), 4),
            "variation_30_bougies_pct": round(float((close.iloc[-1] / close.iloc[-30] - 1) * 100), 2)
            if len(close) >= 30 else None,
            "plus_haut_recent": round(float(recent["high"].max()), 4),
            "plus_bas_recent": round(float(recent["low"].min()), 4),
            "volume_moyen": round(float(recent["volume"].mean()), 2),
            "ma20": round(float(close.rolling(20).mean().iloc[-1]), 4) if len(close) >= 20 else None,
            "ma50": round(float(close.rolling(50).mean().iloc[-1]), 4) if len(close) >= 50 else None,
        }
        return json.dumps(summary, ensure_ascii=False)

    def analyze(self, symbol: str, df: pd.DataFrame) -> ClaudeAnalysis:
        """
        Analyse une paire et renvoie une recommandation.

        Utilise Claude si une clé est configurée, sinon le fallback technique.
        """
        if self._client is None:
            return self._fallback_analysis(symbol, df, reason="Pas de clé Claude configurée")

        market = self._build_market_summary(symbol, df)
        try:
            message = self._client.messages.create(
                model=settings.anthropic_model,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Données de marché à analyser :\n{market}",
                }],
            )
            text = message.content[0].text.strip()
            data = json.loads(self._extract_json(text))
            return ClaudeAnalysis(
                action=Action(data["action"]),
                conviction=max(0.0, min(1.0, float(data["conviction"]))),
                stop_loss_pct=max(0.001, float(data["stop_loss_pct"])),
                reasoning=str(data.get("reasoning", "")),
                source="claude",
            )
        except Exception as exc:  # noqa: BLE001 — on ne veut jamais planter la boucle
            logger.warning("Analyse Claude échouée (%s) — fallback technique.", exc)
            return self._fallback_analysis(symbol, df, reason=f"Erreur Claude: {exc}")

    def _fallback_analysis(self, symbol: str, df: pd.DataFrame, reason: str) -> ClaudeAnalysis:
        """Analyse de secours 100 % locale via une stratégie technique."""
        sig: Signal = self._fallback.generate(df)
        return ClaudeAnalysis(
            action=sig.action,
            conviction=sig.conviction,
            stop_loss_pct=sig.stop_loss_pct,
            reasoning=f"[Fallback technique] {sig.reason} ({reason})",
            source="fallback",
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extrait le premier objet JSON d'une réponse (robustesse)."""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Aucun JSON dans la réponse")
        return text[start : end + 1]
