"""
auto-update/scanner.py
======================
Agent de veille hebdomadaire.

Rôle :
  1. Scanner les repos GitHub finance/trading les plus étoilés et les
     nouvelles stratégies de l'écosystème Freqtrade.
  2. Résumer les nouveautés via l'API Claude.
  3. Proposer une intégration sous forme de rapport — JAMAIS d'auto-merge en
     prod sans validation humaine (règle explicite).

Le résultat est écrit dans `auto-update/reports/` (Markdown) et une alerte
est envoyée. Aucune modification du code de trading n'est effectuée
automatiquement.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import requests

from core import get_logger, send_alert, settings

logger = get_logger("auto-update")

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Requêtes de recherche GitHub ciblant le trading algorithmique.
_SEARCH_QUERIES = [
    "algorithmic trading crypto",
    "freqtrade strategy",
    "quantitative trading",
    "trading bot ccxt",
]

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


def scan_github(min_stars: int = 500, per_query: int = 5) -> List[dict]:
    """
    Interroge l'API de recherche GitHub pour les repos trading étoilés.

    N'exige pas de token (limite basse de rate limit) mais l'utilise s'il est
    présent via la variable d'environnement GITHUB_TOKEN.
    """
    import os

    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results: List[dict] = []
    for query in _SEARCH_QUERIES:
        params = {
            "q": f"{query} stars:>={min_stars}",
            "sort": "updated",   # les plus récemment mis à jour
            "order": "desc",
            "per_page": per_query,
        }
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                headers=headers, params=params, timeout=15,
            )
            resp.raise_for_status()
            for repo in resp.json().get("items", []):
                results.append({
                    "name": repo["full_name"],
                    "stars": repo["stargazers_count"],
                    "description": repo.get("description") or "",
                    "url": repo["html_url"],
                    "updated_at": repo["updated_at"],
                    "query": query,
                })
        except requests.RequestException as exc:
            logger.warning("Recherche GitHub échouée (%s): %s", query, exc)

    # Déduplication par nom de repo, tri par étoiles décroissantes.
    unique = {r["name"]: r for r in results}
    return sorted(unique.values(), key=lambda r: r["stars"], reverse=True)


def summarize_with_claude(repos: List[dict]) -> str:
    """
    Résume les nouveautés via Claude et propose des pistes d'intégration.

    Fallback : si aucune clé Claude n'est configurée, produit un résumé
    tabulaire simple sans IA.
    """
    if not (anthropic and settings.anthropic_api_key):
        logger.info("Pas de clé Claude — résumé simple sans IA.")
        lines = ["## Veille (résumé sans IA)\n"]
        for r in repos[:15]:
            lines.append(f"- **[{r['name']}]({r['url']})** ⭐{r['stars']} — {r['description']}")
        return "\n".join(lines)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    payload = json.dumps(repos[:20], ensure_ascii=False, indent=2)
    prompt = (
        "Voici une liste de repos GitHub de trading algorithmique récemment "
        "mis à jour. Rédige en français une synthèse de veille pour une "
        "trader crypto : regroupe par thème (stratégies, infra, data, IA), "
        "signale 3 à 5 pistes d'intégration concrètes pour un bot basé sur "
        "CCXT + Freqtrade, et indique clairement les risques. NE PROPOSE "
        "JAMAIS de merge automatique en production : chaque intégration doit "
        "être validée manuellement puis backtestée sur 12 mois.\n\n"
        f"Données :\n{payload}"
    )
    try:
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as exc:  # noqa: BLE001
        logger.warning("Synthèse Claude échouée: %s", exc)
        return f"Synthèse IA indisponible ({exc}). Repos bruts:\n" + payload


def write_report(summary: str, repos: List[dict]) -> Path:
    """Écrit le rapport de veille Markdown et déclenche une alerte."""
    now = datetime.now(timezone.utc)
    report_path = REPORTS_DIR / f"veille_{now:%Y-%m-%d}.md"
    header = (
        f"# Rapport de veille — {now:%Y-%m-%d}\n\n"
        f"{len(repos)} repos analysés. **Aucune intégration automatique** : "
        "les propositions ci-dessous exigent une validation humaine puis un "
        "backtest 12 mois avant tout passage en live (règles n°5 et veille).\n\n"
    )
    report_path.write_text(header + summary + "\n", encoding="utf-8")
    logger.info("Rapport de veille écrit: %s", report_path)
    send_alert(f"Nouveau rapport de veille disponible: {report_path.name}", level="INFO")
    return report_path


def run_weekly_scan() -> Path:
    """Exécute le cycle complet de veille (à planifier chaque semaine)."""
    logger.info("Démarrage du scan de veille hebdomadaire…")
    repos = scan_github()
    summary = summarize_with_claude(repos)
    return write_report(summary, repos)


if __name__ == "__main__":
    run_weekly_scan()
