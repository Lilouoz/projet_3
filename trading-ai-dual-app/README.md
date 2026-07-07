# 🤖 trading-ai-dual-app

Monorepo Python de **deux applications de trading crypto assistées par IA**,
multi-exchange (via [CCXT](https://github.com/ccxt/ccxt)), avec gestion du
risque intégrée, backtesting Freqtrade et tableau de bord de pilotage en
temps réel.

> ⚠️ **Sécurité d'abord.** L'ensemble démarre **en paper trading**. Aucun
> ordre réel n'est passé tant que le live n'est pas explicitement autorisé
> (deux verrous : `.env` **et** confirmation dans le dashboard).

---

## 🎯 Les deux applications

| App | Horizon | Principe | IA |
|-----|---------|----------|----|
| **app-scalp** | secondes | Suit le carnet d'ordres (websocket/REST), détecte micro-spreads + momentum court, exécute automatiquement. | Non |
| **app-swing** | minutes–heures | OHLCV toutes les 5 min analysé par **Claude** (momentum, divergences, supports/résistances) → BUY/SELL/HOLD + conviction. Exécution auto si conviction > seuil, sinon validation manuelle. | Oui (Claude) |

---

## 🧱 Structure du monorepo

```
trading-ai-dual-app/
├── core/          Connecteurs CCXT multi-exchange, .env, risk management, logger CSV + alertes
├── app-scalp/     App 1 — scalping haute fréquence (carnet d'ordres)
├── app-swing/     App 2 — swing trading analysé par Claude
├── backtest/      Moteur de backtesting basé sur Freqtrade (rapports HTML : Sharpe, win rate, drawdown, profit factor)
├── strategies/    Stratégies éprouvées unifiées : mean reversion, momentum, grid, arbitrage triangulaire
├── auto-update/   Agent de veille hebdomadaire (GitHub + Freqtrade) → synthèse Claude, jamais d'auto-merge
├── dashboard/     FastAPI + UI web : réglages live, on/off, P&L temps réel, historique
└── docs/          SETUP.md (clés API, installation, lancement, paramétrage, push GitHub)
```

---

## 🔒 Règles non négociables (implémentées)

1. **Paper trading par défaut.** Live = `LIVE_TRADING=true` dans `.env`
   **ET** confirmation dans le dashboard. → `core/config.py::can_trade_live`
2. **Aucune clé API en dur.** Tout en `.env` (jamais commité), `.env.example`
   fourni. → `.gitignore`, `core/config.py`
3. **Kill-switch global** si le drawdown journalier dépasse **5 %**.
   → `core/risk.py::RiskManager`
4. **Stop-loss attaché à chaque ordre** dès sa création, jamais après.
   → `core/exchange.py::place_order`
5. **Backtest 12 mois** obligatoire avant d'autoriser une stratégie en live.
   → `backtest/run_backtest.py` (jeton d'autorisation)
6. **Code commenté en français, README en français.** ✅

Autre garde-fou : **position sizing à 2 %** du capital par trade
(`RISK_PER_TRADE`, modifiable en live).

---

## 🚀 Démarrage rapide

```bash
# 1. Dépendances
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env      # puis renseignez vos clés API (permission TRADE only)

# 3. Lancement (ou : docker compose up --build)
python -m uvicorn dashboard.app:app --port 8000   # dashboard → http://localhost:8000
python app-swing/main.py                           # app swing
python app-scalp/main.py                           # app scalp (optionnelle)
```

Guide complet (création des clés par exchange, Docker, paramétrage, push
GitHub) : **[docs/SETUP.md](docs/SETUP.md)**.

---

## 📊 Backtesting (basé sur Freqtrade)

```bash
python -m backtest.run_backtest --strategy MeanReversionStrategy \
    --pairs BTC/USDT ETH/USDT --authorize
```

Freqtrade n'est **pas réécrit** : il est installé comme dépendance et fournit
les rapports (Sharpe, win rate, max drawdown, profit factor). Détails :
[backtest/README.md](backtest/README.md).

---

## 🖥️ Dashboard

- Sliders/champs modifiables **en live** (paires, taille de position, seuil
  de conviction, spread min).
- Panneau **Money management** piloté par l'utilisatrice : **mise de départ**,
  **risque par trade** (borné à 10 %), **drawdown journalier max** (kill-switch).
- Panneau **Performance réelle (frais déduits)** : par position → P&L brut,
  frais, **P&L net (gain réel)**, rendement ; synthèse globale → capital
  actuel, **rendement en % sur la mise de départ**, réalisé vs latent, frais
  cumulés.
- Interrupteurs **on/off par application et par exchange**.
- Historique des trades, confirmation du passage **LIVE**, réarmement du
  **kill-switch**.

---

## 🔑 Exchanges supportés

Crypto.com · Binance · Pionex · Bybit · Kraken — via CCXT, unifiés dans
`core/exchange.py`. Activez-les dans `.env` (`<EXCHANGE>_ENABLED=true`) ou
depuis le dashboard.

---

## ⚖️ Avertissement

Le trading de cryptomonnaies comporte un **risque de perte en capital**. Ce
logiciel est fourni à titre éducatif et expérimental. Testez longuement en
paper trading, backtestez chaque stratégie, et n'engagez jamais plus que ce
que vous pouvez vous permettre de perdre.
