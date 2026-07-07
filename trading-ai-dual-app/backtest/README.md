# /backtest — Moteur de backtesting (basé sur Freqtrade)

Ce module **n'implémente pas** son propre moteur de backtest : il s'appuie
sur **[Freqtrade](https://www.freqtrade.io/)**, installé comme dépendance
(voir `requirements.txt`). On profite ainsi d'un moteur éprouvé, de ses
rapports HTML interactifs (Plotly) et de son écosystème de stratégies.

## Rôle

- Télécharger les données historiques **Binance / Crypto.com** (12 mois).
- Backtester chaque stratégie du dossier `/strategies` (règle non
  négociable n°5 : **12 mois de backtest avant toute autorisation live**).
- Produire des **rapports HTML** avec Sharpe, win rate, max drawdown,
  profit factor.
- Écrire un **jeton d'autorisation** (`authorized/<Strategy>.json`) lu par
  les applications avant d'autoriser une stratégie en live.

## Installation de Freqtrade

Freqtrade nécessite TA-Lib (dépendance système). La méthode recommandée :

```bash
# Depuis la racine du monorepo
pip install -r requirements.txt

# Si TA-Lib pose problème, utilisez le script officiel Freqtrade :
#   https://www.freqtrade.io/en/stable/installation/
# ou l'image Docker (voir docker-compose.yml, service `backtest`).
```

## Structure `user_data`

Freqtrade travaille dans `user_data/` :

```
user_data/
  strategies/   → stratégies Freqtrade (symlink/copie depuis /strategies)
  data/         → données OHLCV téléchargées (ignoré par git)
  backtest_results/ → résultats bruts (ignoré par git)
  plot/         → rapports HTML générés (ignoré par git)
```

## Utilisation

```bash
# Backtest sur 12 mois glissants (par défaut) puis autorisation live
python -m backtest.run_backtest \
    --strategy MeanReversionStrategy \
    --pairs BTC/USDT ETH/USDT \
    --timeframe 5m \
    --authorize

# Plage explicite + exchange Crypto.com
python -m backtest.run_backtest \
    --strategy MomentumStrategy \
    --timerange 20240101-20250101 \
    --exchange cryptocom
```

Le drapeau `--authorize` n'écrit le jeton d'autorisation live **que si le
backtest réussit**. Sans jeton, les applications refusent de trader la
stratégie en réel.

## Rapports

Freqtrade génère nativement :

- Un tableau de métriques dans la console (Sharpe, Sortino, Calmar,
  win rate, profit factor, max drawdown, etc.).
- Un graphique HTML interactif via `plot-profit`
  (`user_data/plot/freqtrade-profit-plot.html`).
