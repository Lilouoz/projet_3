# 🤖 trading-ai-dual-app

Monorepo Python de **deux applications de trading crypto assistées par IA**,
multi-exchange (via [CCXT](https://github.com/ccxt/ccxt)), avec gestion du
risque intégrée, backtesting Freqtrade et tableau de bord de pilotage en
temps réel.

> ⚠️ **Sécurité d'abord.** L'ensemble démarre **en paper trading**. Aucun
> ordre réel n'est passé tant que le live n'est pas explicitement autorisé
> (deux verrous : `.env` **et** confirmation dans le dashboard).

## 🧭 Principe fondateur (non négociable)

**Le LLM analyse, il n'exécute JAMAIS.** Toute exécution passe par un
**moteur de règles déterministe** (`core/decision.py`) qui valide seul :
sizing (Kelly), stop-loss, exposition totale, cohérence du signal
(conviction ≥ seuil **ET** confirmation technique), rentabilité nette.
Aucun ordre ne peut être placé sur la seule sortie d'un LLM.

---

## 🎯 Les deux applications

| App | Horizon | Principe | LLM |
|-----|---------|----------|----|
| **app-scalp** | secondes | Carnet d'ordres (websocket/REST), micro-spreads + momentum court. **Zéro LLM** dans la boucle rapide (latence incompatible). Exécution par règles pures via le moteur de décision. | Non |
| **app-swing** | minutes–heures | OHLCV 5 min + positions des whales. Claude produit une **ANALYSE JSON** (thèse, conviction 0-100, invalidation, niveaux). Le **moteur de décision** décide seul (conviction ≥ seuil ET confirmation technique ET risk check). Mode manuel possible. | Analyste only |

---

## 🧱 Structure du monorepo

```
trading-ai-dual-app/
├── core/               Connecteurs CCXT, .env, risk management, moteur de décision déterministe, logger
│   ├── decision.py     Moteur de règles : le LLM n'exécute jamais, tout passe par ici
│   ├── sizing/         Kelly Criterion fractionnaire (half-Kelly), plafonds 6% / 2%
│   └── whale_tracker/  Copy-trading : Hyperliquid + wallets on-chain, scoring, sortie anticipée
├── app-scalp/     App 1 — scalping haute fréquence, zéro LLM (règles pures)
├── app-swing/     App 2 — Claude analyste (JSON) + moteur de décision, + copy-trading
├── backtest/      Freqtrade (dépendance) : rapports HTML + calcul des paramètres Kelly
├── strategies/    mean reversion, momentum, grid, arbitrage triangulaire, whale-follow
├── auto-update/   Veille hebdo GitHub/Freqtrade → synthèse Claude, intégration en branche séparée
├── dashboard/     FastAPI + UI : sliders live (Kelly, exposition…), wallets suivis + scores, P&L
└── docs/          SETUP.md (clés API, install, lancement, ajout de wallets, push GitHub)
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

Garde-fous supplémentaires :
- **Sizing Kelly fractionnaire** (half-Kelly par défaut) plafonné à **6 %**
  du capital par position et **2 %** de risque réel par trade
  (`core/sizing`). Les paramètres W/R viennent du backtest.
- **Timeout LLM strict de 10 s** (règle n°6) : pas de réponse = pas de
  trade, jamais de position par défaut (`core/decision.py`, `analyzer.py`).
- **Exposition totale plafonnée** (somme des positions, `MAX_TOTAL_EXPOSURE_PCT`).

### 💸 Rentabilité nette adaptative (fee-aware)

Chaque ordre passe par un **filtre de rentabilité** qui s'adapte en temps réel
au **modèle de frais de chaque plateforme** :

- Frais récupérés automatiquement via CCXT à la connexion, ou saisis
  (`<EXCHANGE>_TAKER_FEE`), ou par défaut indicatif.
- **Forfait illimité** sans frais par trade : `<EXCHANGE>_FLAT_FEE=true` →
  coût marginal nul, il suffit que le trade soit **positif** (idéal
  micro-trading).
- Filtre : un trade n'est exécuté que si `gain attendu − frais aller-retour
  ≥ marge nette min.` (`MIN_NET_MARGIN`, `0` = juste être positif).
- Le dashboard évalue **en direct et par plateforme** l'edge net et désigne
  la plus avantageuse (`core/exchange.py::evaluate_profitability`).
- Le **backtest** est fee-aware (`--fee`) pour valider la rentabilité NETTE
  sur 12 mois avant le live.

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
- Panneau **Money management** : **mise de départ**, **risque par trade**,
  **drawdown max**, **fraction de Kelly**, **plafond par position**,
  **exposition totale max**.
- Panneau **🐋 Wallets suivis** : ajout/suppression/on-off des wallets
  copiés, avec leur **score glissant 30 j** (winrate, PnL, drawdown) et leurs
  positions ; désactivation automatique sous les seuils.
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
