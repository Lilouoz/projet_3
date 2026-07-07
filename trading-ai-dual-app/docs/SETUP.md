# Guide d'installation & de paramétrage — trading-ai-dual-app

Ce guide couvre : la création des clés API par exchange, l'installation, le
lancement des applications, le paramétrage en live et la publication sur
GitHub.

> ⚠️ **Sécurité avant tout.** Ce logiciel manipule potentiellement de
> l'argent réel. Il démarre **toujours en mode paper trading** et n'effectue
> aucun ordre réel tant que vous ne l'avez pas explicitement autorisé
> (deux verrous). Lisez ce guide en entier avant de passer en live.

---

## 1. Prérequis

- Python 3.11 ou supérieur
- `git`
- (Optionnel mais recommandé) Docker + docker-compose
- Une clé API Anthropic (Claude) pour l'analyse de l'app-swing et la veille

---

## 2. Création des clés API par exchange

> **Règle absolue : permission `trade` UNIQUEMENT, jamais `withdrawal`
> (retrait).** Aucune clé ne doit pouvoir sortir des fonds de la plateforme.
> Restreignez aussi par adresse IP quand c'est possible.

### Binance
1. Profil → **API Management** → *Create API*.
2. Cochez **Enable Spot & Margin Trading**.
3. **NE cochez PAS** *Enable Withdrawals*.
4. Ajoutez une **restriction d'IP** (IP de votre serveur).
5. Copiez `API Key` et `Secret Key` → `BINANCE_API_KEY`, `BINANCE_API_SECRET`.

### Crypto.com (Exchange)
1. Settings → **API Keys** → *Create a New API Key*.
2. Permissions : activez **Trade**, laissez **Withdraw désactivé**.
3. Renseignez `CRYPTOCOM_API_KEY`, `CRYPTOCOM_API_SECRET`
   (et `CRYPTOCOM_API_PASSWORD` si un passphrase est demandé).

### Pionex
1. Account → **API Management** → *Create API*.
2. Permission **Trade** uniquement (pas de retrait).
3. Renseignez `PIONEX_API_KEY`, `PIONEX_API_SECRET`.

### Bybit
1. Account & Security → **API** → *Create New Key*.
2. Type : *System-generated*, permission **Trade** (Spot), pas de *Withdraw*.
3. Restriction IP recommandée.
4. Renseignez `BYBIT_API_KEY`, `BYBIT_API_SECRET`.

### Kraken
1. Settings → **API** → *Add key*.
2. Permissions : **Create & Modify Orders**, **Query Open/Closed Orders**.
   NE cochez PAS *Withdraw Funds*.
3. Renseignez `KRAKEN_API_KEY`, `KRAKEN_API_SECRET`.

Après création, mettez `<EXCHANGE>_ENABLED=true` dans `.env` pour activer un
exchange (ou activez-le en live depuis le dashboard).

---

## 3. Installation

```bash
# 1. Cloner le dépôt
git clone <votre-repo>.git
cd trading-ai-dual-app

# 2. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Copier le modèle de configuration et le remplir
cp .env.example .env
#   → éditez .env : clés API, ANTHROPIC_API_KEY, paires, etc.
```

> **Freqtrade** (module `/backtest`) nécessite TA-Lib (dépendance système).
> En cas de souci d'installation, utilisez l'image Docker (section 6) ou
> suivez la doc officielle : <https://www.freqtrade.io/en/stable/installation/>.

---

## 4. Lancement

Chaque composant se lance séparément (ou tous ensemble via Docker).

```bash
# Le dashboard (interface de pilotage) — http://localhost:8000
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8000

# App swing (analyse Claude toutes les 5 min)
python app-swing/main.py

# App scalp (haute fréquence)
python app-scalp/main.py

# Agent de veille (scan hebdomadaire)
python auto-update/scheduler.py
```

> Astuce : lancez d'abord le **dashboard**, ajustez les paramètres, activez
> les exchanges, puis démarrez les applications.

---

## 5. Paramétrage en live (sans redémarrage)

Ouvrez le dashboard sur <http://localhost:8000>. Vous pouvez modifier **en
direct**, sans redémarrer les applications :

- **Paires actives** (ex. `BTC/USDT,ETH/USDT`)
- **Taille de position** (USD)
- **Seuil de conviction** de l'app-swing (exécution auto au-dessus, sinon
  validation manuelle)
- **Spread minimal** de l'app-scalp
- **Risque par trade** (défaut 2 %)
- **On/Off par application** et **par exchange**

### Passer en trading réel (LIVE) — double verrou

1. Mettez `LIVE_TRADING=true` dans `.env` **et redémarrez** les apps.
2. Dans le dashboard, cliquez **« Confirmer LIVE »**.

Tant que ces **deux** conditions ne sont pas réunies, tout reste en paper
trading. À tout moment, « Revenir en PAPER » ré-arme le filet de sécurité.

### Kill-switch

Si le **drawdown journalier dépasse 5 %**, le kill-switch coupe
automatiquement tout trading. Après vérification, vous pouvez le réarmer
depuis le dashboard (« Réarmer après kill-switch »).

---

## 5 bis. Ajouter des wallets à suivre (copy-trading)

Le module whale-tracker copie les positions de traders performants, après
validation par le moteur de décision (jamais de copie aveugle).

**Deux sources, toutes deux gratuites :**

1. **Hyperliquid** (positions publiques) — aucune clé requise. Dans le
   dashboard, panneau **🐋 Wallets suivis** :
   - Collez l'adresse du trader, choisissez source **Hyperliquid**, cliquez
     **➕ Suivre**.

2. **Wallets on-chain** (Ethereum / Polygon) — clé d'explorateur gratuite
   recommandée :
   - Créez une clé gratuite sur [etherscan.io](https://etherscan.io/apis) et/ou
     [polygonscan.com](https://polygonscan.com/apis).
   - Renseignez `ETHERSCAN_API_KEY` / `POLYGONSCAN_API_KEY` dans `.env`.
   - Dans le dashboard, ajoutez l'adresse avec source **On-chain** et la chaîne.

**Scoring et sécurité :**

- Chaque wallet est noté sur **30 jours glissants** (winrate, PnL, drawdown).
- Un wallet sous les seuils (`WHALE_MIN_WINRATE`, `WHALE_MAX_DRAWDOWN`…) est
  **désactivé automatiquement** (badge `auto-off`).
- La position copiée est **fermée par anticipation** dès que le wallet source
  réduit sa position **ou** que le momentum se retourne.

Cliquez **↻ Scores** pour forcer un rafraîchissement.

## 6. Lancement via Docker

```bash
# Construit les images et lance dashboard + apps + veille
docker compose up --build

# Dashboard : http://localhost:8000
```

Le fichier `.env` est monté automatiquement (voir `docker-compose.yml`).

---

## 7. Backtester une stratégie (obligatoire avant le live)

**Règle non négociable n°5** : 12 mois de backtest avant toute autorisation
live.

```bash
python -m backtest.run_backtest \
    --strategy MeanReversionStrategy \
    --pairs BTC/USDT ETH/USDT \
    --authorize
```

Le drapeau `--authorize` n'écrit le jeton d'autorisation **que si le
backtest réussit**. Voir `backtest/README.md`.

---

## 8. Publier sur GitHub (repo vierge)

```bash
# Depuis la racine du monorepo (le dépôt git est déjà initialisé)
git remote add origin https://github.com/<votre-utilisateur>/<votre-repo>.git
git branch -M main
git push -u origin main
```

> Vérifiez que `.env` **n'est pas** suivi par git (`git status`). Il est
> exclu via `.gitignore`. Ne poussez **jamais** vos clés API.

---

## 9. Rappel des règles de sécurité

1. **Paper trading par défaut** ; live = `.env` + confirmation dashboard.
2. **Aucune clé en dur** : tout dans `.env` (jamais commité).
3. **Kill-switch** global si drawdown journalier > 5 %.
4. **Stop-loss attaché à chaque ordre** dès sa création, jamais après.
5. **Backtest 12 mois** avant d'autoriser une stratégie en live.
6. **Timeout LLM strict (10 s)** : pas de réponse = pas de trade, jamais de
   position par défaut.
7. Le **LLM n'exécute jamais** : toute exécution passe par le moteur de
   décision déterministe (`core/decision.py`).
