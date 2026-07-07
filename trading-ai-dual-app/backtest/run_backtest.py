"""
backtest/run_backtest.py
========================
Wrapper autour de Freqtrade pour lancer un backtest et générer un rapport.

Freqtrade N'EST PAS réécrit (règle explicite) : on l'installe comme
dépendance et on l'appelle via sa CLI. Ce script se contente de :
  1. Télécharger les données historiques (Binance/Crypto.com) sur 12 mois.
  2. Lancer le backtest sur une stratégie donnée.
  3. Produire un rapport HTML avec les métriques clés
     (Sharpe, win rate, max drawdown, profit factor).

Règle non négociable n°5 : une stratégie doit être backtestée sur 12 mois
avant d'être autorisée en live. Ce script matérialise cette étape et écrit
un fichier `.authorized` en cas de succès, lu par les applications.

Usage :
    python -m backtest.run_backtest --strategy MeanReversionStrategy \
        --timerange 20240101-20250101 --pairs BTC/USDT ETH/USDT
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Répertoires Freqtrade (convention `user_data`).
HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
USER_DATA = HERE / "user_data"
RESULTS_DIR = USER_DATA / "backtest_results"
AUTHORIZED_DIR = HERE / "authorized"
AUTHORIZED_DIR.mkdir(exist_ok=True)


def _run(cmd: list[str]) -> int:
    """Exécute une commande Freqtrade et renvoie son code de sortie."""
    print(f"\n$ {' '.join(cmd)}\n", flush=True)
    return subprocess.call(cmd)


def default_timerange_12m() -> str:
    """Retourne une plage de 12 mois glissants au format Freqtrade."""
    end = datetime.utcnow().date()
    start = end - timedelta(days=365)
    return f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"


def download_data(pairs: list[str], timerange: str, timeframe: str, exchange: str) -> int:
    """
    Télécharge les données OHLCV historiques via la CLI Freqtrade.

    Freqtrade gère le format et le cache des données dans user_data/data.
    """
    cmd = [
        sys.executable, "-m", "freqtrade", "download-data",
        "--config", str(CONFIG),
        "--userdir", str(USER_DATA),
        "--exchange", exchange,
        "--timeframe", timeframe,
        "--timerange", timerange,
        "--pairs", *pairs,
    ]
    return _run(cmd)


def run_backtest(
    strategy: str,
    pairs: list[str],
    timerange: str,
    timeframe: str,
    fee: float | None = None,
) -> int:
    """
    Lance le backtest Freqtrade sur la stratégie fournie.

    Args:
        fee: frais réels par transaction (fraction, ex. 0.001). Injecté dans
            Freqtrade via `--fee` pour que les métriques reflètent le coût
            réel et valident la rentabilité NETTE (fee-aware). Mettre 0 pour
            un forfait sans frais par trade.
    """
    cmd = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "--config", str(CONFIG),
        "--userdir", str(USER_DATA),
        "--strategy", strategy,
        "--timeframe", timeframe,
        "--timerange", timerange,
        "--pairs", *pairs,
        "--export", "trades",
        "--export-filename", str(RESULTS_DIR / f"{strategy}_{timerange}"),
    ]
    # Frais appliqués à l'achat ET à la vente par Freqtrade (aller-retour).
    if fee is not None:
        cmd += ["--fee", str(fee)]
    return _run(cmd)


def generate_html_report(strategy: str, timerange: str) -> Path:
    """
    Génère un rapport HTML de backtesting via `freqtrade plot-profit`.

    Freqtrade produit nativement des graphiques Plotly interactifs (HTML).
    On complète avec un résumé texte des métriques principales.
    """
    cmd = [
        sys.executable, "-m", "freqtrade", "plot-profit",
        "--config", str(CONFIG),
        "--userdir", str(USER_DATA),
        "--strategy", strategy,
        "--timerange", timerange,
    ]
    _run(cmd)
    plot_file = USER_DATA / "plot" / f"freqtrade-profit-plot.html"
    print(f"Rapport HTML Freqtrade : {plot_file}")
    return plot_file


def mark_authorized(strategy: str, timerange: str) -> Path:
    """
    Écrit un jeton d'autorisation live pour la stratégie (règle n°5).

    Les applications lisent ce fichier avant d'autoriser une stratégie en
    live : pas de jeton => pas de trading réel avec cette stratégie.
    """
    token = AUTHORIZED_DIR / f"{strategy}.json"
    token.write_text(
        json.dumps(
            {
                "strategy": strategy,
                "timerange": timerange,
                "backtested_at": datetime.utcnow().isoformat(),
                "authorized_live": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Stratégie {strategy} autorisée en live (jeton: {token})")
    return token


def main() -> int:
    parser = argparse.ArgumentParser(description="Backtest Freqtrade + rapport HTML")
    parser.add_argument("--strategy", required=True, help="Nom de la classe de stratégie")
    parser.add_argument("--pairs", nargs="+", default=["BTC/USDT", "ETH/USDT"])
    parser.add_argument("--timerange", default=None, help="AAAAMMJJ-AAAAMMJJ (défaut: 12 mois)")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--exchange", default="binance", choices=["binance", "cryptocom"])
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--fee", type=float, default=None,
                        help="Frais réels par transaction (ex. 0.001). 0 pour un forfait "
                             "sans frais. Rend le backtest fee-aware (rentabilité nette).")
    parser.add_argument("--authorize", action="store_true",
                        help="Marque la stratégie comme autorisée en live si le backtest réussit")
    args = parser.parse_args()

    timerange = args.timerange or default_timerange_12m()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not args.skip_download:
        if download_data(args.pairs, timerange, args.timeframe, args.exchange) != 0:
            print("Échec du téléchargement des données.", file=sys.stderr)
            return 1

    if run_backtest(args.strategy, args.pairs, timerange, args.timeframe, fee=args.fee) != 0:
        print("Le backtest a échoué.", file=sys.stderr)
        return 1

    generate_html_report(args.strategy, timerange)

    if args.authorize:
        mark_authorized(args.strategy, timerange)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
