"""
Package `core` — briques communes aux deux applications de trading.

Expose les objets partagés :
  - `settings`        : réglages globaux modifiables en live
  - `EXCHANGES`       : credentials par exchange (depuis .env)
  - `risk_manager`    : gestionnaire de risque (sizing 2%, stop-loss, kill-switch)
  - `registry`        : registre des connecteurs CCXT multi-exchange
  - `get_logger`      : fabrique de loggers
"""

from .config import settings, EXCHANGES, Settings, ExchangeConfig
from .risk import risk_manager, RiskManager, OrderPlan, RiskViolation
from .exchange import registry, ExchangeConnector, ExchangeRegistry
from .logger import get_logger, log_trade, send_alert
from .portfolio import portfolio, Portfolio, Position, ClosedTrade

# Initialise la mise de départ du portefeuille à partir des réglages, afin
# que le rendement (%) affiché dans le dashboard ait une base correcte.
portfolio.set_starting_capital(settings.starting_capital)

__all__ = [
    "settings",
    "EXCHANGES",
    "Settings",
    "ExchangeConfig",
    "risk_manager",
    "RiskManager",
    "OrderPlan",
    "RiskViolation",
    "registry",
    "ExchangeConnector",
    "ExchangeRegistry",
    "get_logger",
    "log_trade",
    "send_alert",
    "portfolio",
    "Portfolio",
    "Position",
    "ClosedTrade",
]
