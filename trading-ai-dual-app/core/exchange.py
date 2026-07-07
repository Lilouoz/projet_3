"""
core/exchange.py
================
Connecteurs CCXT multi-exchange (Crypto.com, Binance, Pionex, Bybit, Kraken).

Responsabilités :
  - Instancier un client CCXT par exchange avec les clés lues dans .env.
  - Basculer automatiquement en mode TESTNET/paper si le live n'est pas
    explicitement autorisé (règle non négociable n°1).
  - Passer chaque ordre AVEC son stop-loss attaché dès la création (règle
    n°4) — jamais en deux temps.
  - Fournir un mode paper trading interne (simulation) quand la plateforme
    ne propose pas de testnet.

Toutes les méthodes de trading passent par `place_order`, qui exige un
`OrderPlan` déjà validé par le `RiskManager`.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import ccxt

from .config import EXCHANGES, ExchangeConfig, settings
from .logger import get_logger, log_trade, send_alert
from .risk import OrderPlan, RiskViolation

logger = get_logger("exchange")

# Exchanges pour lesquels CCXT expose un mode sandbox/testnet natif.
_TESTNET_CAPABLE = {"binance", "bybit", "kraken"}


class ExchangeConnector:
    """
    Enveloppe un client CCXT pour un exchange donné.

    Gère la connexion, le mode paper/live et le passage d'ordres avec
    stop-loss attaché.
    """

    def __init__(self, config: ExchangeConfig) -> None:
        self.config = config
        self.name = config.name
        self._client: Optional[ccxt.Exchange] = None
        # Positions simulées en mode paper : {symbol: dict}.
        self._paper_positions: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Connexion
    # ------------------------------------------------------------------
    @property
    def is_live(self) -> bool:
        """Vrai si CET exchange opère en réel (double condition globale)."""
        return settings.can_trade_live() and self.config.enabled

    def connect(self) -> Optional[ccxt.Exchange]:
        """
        Instancie (paresseusement) le client CCXT.

        Retourne None si l'exchange n'est pas supporté par CCXT ou si les
        clés manquent en mode live.
        """
        if self._client is not None:
            return self._client

        exchange_cls = getattr(ccxt, self.name, None)
        if exchange_cls is None:
            logger.error("Exchange %s non supporté par CCXT.", self.name)
            return None

        params = {
            "apiKey": self.config.api_key,
            "secret": self.config.api_secret,
            "enableRateLimit": True,
        }
        if self.config.api_password:
            params["password"] = self.config.api_password

        client = exchange_cls(params)

        # Règle n°1 : si on n'est pas explicitement en live, on force le
        # sandbox/testnet quand il existe. Sinon on reste en paper interne.
        if not self.is_live:
            if self.name in _TESTNET_CAPABLE:
                try:
                    client.set_sandbox_mode(True)
                    logger.info("[%s] Mode TESTNET (sandbox CCXT) activé.", self.name)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[%s] Sandbox indisponible: %s — paper interne.", self.name, exc)
            else:
                logger.info("[%s] Pas de testnet natif — paper trading interne.", self.name)

        self._client = client
        return client

    # ------------------------------------------------------------------
    # Données de marché
    # ------------------------------------------------------------------
    def fetch_ticker(self, symbol: str) -> Optional[dict]:
        """Récupère le ticker courant d'une paire."""
        client = self.connect()
        if client is None:
            return None
        try:
            return client.fetch_ticker(symbol)
        except ccxt.BaseError as exc:
            logger.error("[%s] fetch_ticker(%s) a échoué: %s", self.name, symbol, exc)
            return None

    def fetch_ohlcv(self, symbol: str, timeframe: str = "5m", limit: int = 200) -> List[list]:
        """Récupère les chandeliers OHLCV (utilisé par app-swing / backtest)."""
        client = self.connect()
        if client is None:
            return []
        try:
            return client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except ccxt.BaseError as exc:
            logger.error("[%s] fetch_ohlcv(%s) a échoué: %s", self.name, symbol, exc)
            return []

    def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[dict]:
        """Récupère le carnet d'ordres (utilisé par app-scalp)."""
        client = self.connect()
        if client is None:
            return None
        try:
            return client.fetch_order_book(symbol, limit=limit)
        except ccxt.BaseError as exc:
            logger.error("[%s] fetch_order_book(%s) a échoué: %s", self.name, symbol, exc)
            return None

    def fetch_equity(self, quote: str = "USDT") -> float:
        """
        Estime l'équité disponible dans la devise de cotation.

        En mode paper, retourne un capital simulé fixe (paramétrable).
        En live, lit le solde réel via CCXT.
        """
        if not self.is_live:
            # Capital simulé pour le paper trading / sizing.
            return float(settings.position_size_usd) * 50  # ex: 5000$ simulés
        client = self.connect()
        if client is None:
            return 0.0
        try:
            balance = client.fetch_balance()
            return float(balance.get("total", {}).get(quote, 0.0))
        except ccxt.BaseError as exc:
            logger.error("[%s] fetch_balance a échoué: %s", self.name, exc)
            return 0.0

    # ------------------------------------------------------------------
    # Exécution d'ordres — stop-loss TOUJOURS attaché à la création
    # ------------------------------------------------------------------
    def place_order(self, plan: OrderPlan, app: str, order_type: str = "market") -> dict:
        """
        Passe un ordre à partir d'un plan validé par le risk management.

        Le stop-loss est TOUJOURS transmis dans les paramètres de l'ordre
        (règle n°4 : jamais après coup). En mode paper, l'ordre est simulé
        et journalisé sans appel réseau réel.

        Raises:
            RiskViolation: si le plan ne contient pas de stop-loss.
        """
        if plan.stop_loss is None or plan.stop_loss <= 0:
            raise RiskViolation("Ordre refusé : stop-loss manquant (règle n°4).")

        mode = "live" if self.is_live else "paper"

        # ---- Mode paper : simulation locale --------------------------
        if mode == "paper":
            self._paper_positions[plan.symbol] = {
                "side": plan.side,
                "amount": plan.amount,
                "entry": plan.entry_price,
                "stop_loss": plan.stop_loss,
            }
            log_trade(
                app=app, exchange=self.name, symbol=plan.symbol, side=plan.side,
                amount=plan.amount, price=plan.entry_price, stop_loss=plan.stop_loss,
                order_type=order_type, mode=mode, note="paper-sim",
            )
            logger.info("[PAPER][%s] %s %s x%.6f @ %.4f (SL=%.4f)",
                        self.name, plan.side, plan.symbol, plan.amount,
                        plan.entry_price, plan.stop_loss)
            return {"id": "paper", "status": "simulated", "plan": plan}

        # ---- Mode live : ordre réel avec stop-loss attaché -----------
        client = self.connect()
        if client is None:
            raise RiskViolation(f"[{self.name}] Client indisponible pour ordre live.")

        # On attache le stop-loss dans les params de l'ordre. Les clés
        # exactes varient selon l'exchange ; CCXT unifie 'stopLoss'.
        params = {
            "stopLoss": {
                "type": "market",
                "triggerPrice": plan.stop_loss,
            }
        }
        try:
            order = client.create_order(
                symbol=plan.symbol,
                type=order_type,
                side=plan.side,
                amount=plan.amount,
                price=None if order_type == "market" else plan.entry_price,
                params=params,
            )
        except ccxt.BaseError as exc:
            send_alert(f"[{self.name}] Échec ordre live {plan.symbol}: {exc}", level="CRITICAL")
            raise

        log_trade(
            app=app, exchange=self.name, symbol=plan.symbol, side=plan.side,
            amount=plan.amount, price=plan.entry_price, stop_loss=plan.stop_loss,
            order_type=order_type, mode=mode, note=f"orderId={order.get('id')}",
        )
        logger.info("[LIVE][%s] Ordre passé %s (SL attaché=%.4f)",
                    self.name, order.get("id"), plan.stop_loss)
        return order


class ExchangeRegistry:
    """
    Registre central des connecteurs, un par exchange configuré.

    Les applications passent par ce registre pour récupérer un connecteur.
    """

    def __init__(self) -> None:
        self._connectors: Dict[str, ExchangeConnector] = {
            name: ExchangeConnector(cfg) for name, cfg in EXCHANGES.items()
        }

    def get(self, name: str) -> Optional[ExchangeConnector]:
        """Retourne le connecteur d'un exchange (ou None s'il n'existe pas)."""
        return self._connectors.get(name)

    def enabled_connectors(self) -> List[ExchangeConnector]:
        """Liste des connecteurs dont l'exchange est activé (togglable live)."""
        return [c for c in self._connectors.values() if c.config.enabled]

    def all(self) -> Dict[str, ExchangeConnector]:
        """Retourne tous les connecteurs, activés ou non."""
        return dict(self._connectors)


# Registre global partagé par toutes les applications.
registry = ExchangeRegistry()
