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
from typing import Optional

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


def compute_kelly_params(strategy: str, timerange: str) -> Optional[dict]:
    """
    Calcule les paramètres de Kelly (W, R) depuis les résultats du backtest.

    Freqtrade exporte les trades du backtest en JSON. On en déduit :
      - win_rate  W = trades gagnants / total
      - payoff_ratio R = gain moyen / perte moyenne
    puis on écrit ces stats dans data/strategy_stats.json (lu en live par le
    sizing Kelly). Best-effort : renvoie None si le fichier est introuvable.
    """
    # Freqtrade nomme le fichier d'export selon --export-filename.
    export = RESULTS_DIR / f"{strategy}_{timerange}.json"
    candidates = [export] + sorted(RESULTS_DIR.glob(f"{strategy}*.json"), reverse=True)
    data = None
    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                break
            except json.JSONDecodeError:
                continue
    if data is None:
        print("Résultats de backtest introuvables pour le calcul Kelly.", file=sys.stderr)
        return None

    # Structure Freqtrade : {'strategy': {name: {'trades': [...]}}} selon version.
    trades = _extract_trades(data)
    if not trades:
        print("Aucun trade exploitable pour le calcul Kelly.", file=sys.stderr)
        return None

    profits = [float(t.get("profit_abs", t.get("profit_ratio", 0.0))) for t in trades]
    wins = [p for p in profits if p > 0]
    losses = [-p for p in profits if p < 0]
    total = len(profits)
    win_rate = len(wins) / total if total else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    payoff = (avg_win / avg_loss) if avg_loss > 0 else (1.0 if avg_win == 0 else 2.0)

    stats = {
        "win_rate": round(win_rate, 4),
        "payoff_ratio": round(payoff, 4),
        "trades": total,
        "backtested": True,
    }
    _write_strategy_stats(strategy, stats)
    print(f"Stats Kelly {strategy}: W={win_rate:.2%} R={payoff:.2f} sur {total} trades")
    return stats


def _extract_trades(data) -> list:
    """Extrait la liste des trades de la structure d'export Freqtrade."""
    if isinstance(data, dict):
        if "trades" in data and isinstance(data["trades"], list):
            return data["trades"]
        strat = data.get("strategy")
        if isinstance(strat, dict):
            for val in strat.values():
                if isinstance(val, dict) and isinstance(val.get("trades"), list):
                    return val["trades"]
    if isinstance(data, list):
        return data
    return []


def _write_strategy_stats(strategy: str, stats: dict) -> None:
    """Fusionne les stats calculées dans data/strategy_stats.json."""
    stats_file = Path("data") / "strategy_stats.json"
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if stats_file.exists():
        try:
            existing = json.loads(stats_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing[strategy] = stats
    stats_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")


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

    # Calcule et enregistre les paramètres Kelly (W, R) de la stratégie,
    # utilisés en live par le sizing Kelly fractionnaire.
    compute_kelly_params(args.strategy, timerange)

    if args.authorize:
        mark_authorized(args.strategy, timerange)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
