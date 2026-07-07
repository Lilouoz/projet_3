"""
core/config.py
================
Chargement centralisé de la configuration depuis le fichier `.env`.

Toute la configuration sensible (clés API, mode live/testnet, seuils de
risque) transite par des variables d'environnement. AUCUNE clé n'est jamais
écrite en dur dans le code (règle non négociable n°2).

La configuration est aussi exposée sous forme d'objet modifiable EN LIVE
via le dashboard (règle : paramètres modifiables sans restart). Le module
`live_settings` fournit un dictionnaire partagé thread-safe.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List

from dotenv import load_dotenv

# Charge le fichier .env situé à la racine du monorepo (une seule fois).
load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Convertit une variable d'environnement en booléen de façon robuste."""
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "oui", "on"}


def _env_float(name: str, default: float) -> float:
    """Lit un flottant depuis l'environnement avec valeur par défaut."""
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_list(name: str, default: List[str]) -> List[str]:
    """Lit une liste séparée par des virgules depuis l'environnement."""
    raw = os.getenv(name)
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class ExchangeConfig:
    """Configuration d'un exchange unique (clés API + activation)."""

    name: str                     # identifiant CCXT (ex: 'binance', 'kraken')
    api_key: str = ""             # jamais loggée, jamais commitée
    api_secret: str = ""          # idem
    api_password: str = ""        # certaines plateformes (kraken, cryptocom)
    enabled: bool = False         # exchange actif ou non (togglable en live)
    # Frais réels de TON compte sur cette plateforme (dépend du palier).
    # 0 = non renseigné → on récupère les frais réels via CCXT une fois
    # connecté, sinon on retombe sur une valeur par défaut indicative.
    taker_fee: float = 0.0
    maker_fee: float = 0.0
    # Forfait « illimité » / sans frais par trade : si True, le coût marginal
    # par trade est considéré comme nul (le filtre de rentabilité exige alors
    # simplement que le trade soit positif). Utile pour du micro-trading sous
    # abonnement où les frais ne sont pas prélevés à chaque ordre.
    flat_fee: bool = False

    @property
    def has_credentials(self) -> bool:
        """Vrai si les clés minimales sont présentes."""
        return bool(self.api_key and self.api_secret)


@dataclass
class Settings:
    """
    Réglages globaux de l'application.

    Les champs de cette classe sont modifiables EN LIVE via le dashboard.
    On protège les accès concurrents avec un verrou (`_lock`).
    """

    # ---- Mode de fonctionnement ---------------------------------------
    # Par défaut TESTNET / paper trading (règle non négociable n°1).
    # Le passage en live exige LIVE_TRADING=true DANS .env ET confirmation
    # explicite dans le dashboard (voir `live_confirmed`).
    live_trading: bool = field(default_factory=lambda: _env_bool("LIVE_TRADING", False))
    live_confirmed: bool = False  # confirmation manuelle via le dashboard

    # ---- Risk management (règles non négociables 3, 4, 5) --------------
    risk_per_trade: float = field(default_factory=lambda: _env_float("RISK_PER_TRADE", 0.02))
    max_daily_drawdown: float = field(default_factory=lambda: _env_float("MAX_DAILY_DRAWDOWN", 0.05))
    require_stop_loss: bool = True  # stop-loss obligatoire sur CHAQUE position

    # ---- Paramètres de trading (modifiables en live) ------------------
    active_pairs: List[str] = field(
        default_factory=lambda: _env_list("ACTIVE_PAIRS", ["BTC/USDT", "ETH/USDT"])
    )
    position_size_usd: float = field(default_factory=lambda: _env_float("POSITION_SIZE_USD", 100.0))
    # Mise de départ : capital de référence pour calculer le rendement réel
    # affiché dans le dashboard (P&L en % de la mise initiale).
    starting_capital: float = field(default_factory=lambda: _env_float("STARTING_CAPITAL", 5000.0))
    conviction_threshold: float = field(
        default_factory=lambda: _env_float("CONVICTION_THRESHOLD", 0.7)
    )
    min_spread: float = field(default_factory=lambda: _env_float("MIN_SPREAD", 0.0005))
    # ---- Rentabilité nette (fee-aware) --------------------------------
    # Marge nette minimale exigée APRÈS déduction des frais réels.
    # Défaut 0.0 = « juste être positif » : il suffit que le gain attendu
    # couvre les frais (nuls si forfait illimité). Augmente cette valeur si
    # tu veux exiger un profit net minimal par trade.
    min_net_margin: float = field(default_factory=lambda: _env_float("MIN_NET_MARGIN", 0.0))
    # Ratio gain/risque supposé (cible de profit = ratio × distance du stop),
    # utilisé pour estimer le gain brut attendu d'un trade swing.
    reward_risk_ratio: float = field(default_factory=lambda: _env_float("REWARD_RISK_RATIO", 1.5))

    # ---- Interrupteurs on/off par app ---------------------------------
    scalp_enabled: bool = field(default_factory=lambda: _env_bool("SCALP_ENABLED", False))
    swing_enabled: bool = field(default_factory=lambda: _env_bool("SWING_ENABLED", True))

    # ---- Kill-switch global (activé automatiquement par le risk mgmt) --
    kill_switch: bool = False

    # ---- API Claude (analyse app-swing + auto-update) -----------------
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")
    )

    # ---- Verrou interne (non sérialisé) -------------------------------
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False, compare=False)

    def update(self, **kwargs) -> None:
        """
        Met à jour un ou plusieurs paramètres en live (thread-safe).

        Utilisé par le dashboard : chaque slider/champ appelle cette méthode
        sans redémarrage des applications.
        """
        with self._lock:
            for key, value in kwargs.items():
                if key.startswith("_"):
                    continue  # on ne touche jamais aux champs internes
                if hasattr(self, key):
                    setattr(self, key, value)

    def as_dict(self) -> Dict:
        """Sérialise les réglages pour l'API du dashboard (sans le verrou)."""
        with self._lock:
            data = asdict(self)
            data.pop("_lock", None)
            # On masque la clé Anthropic dans les réponses du dashboard.
            if data.get("anthropic_api_key"):
                data["anthropic_api_key"] = "***"
            return data

    def can_trade_live(self) -> bool:
        """
        Vrai UNIQUEMENT si le trading réel est autorisé.

        Double verrou (règle n°1) : LIVE_TRADING=true dans .env ET
        confirmation manuelle dans le dashboard, et pas de kill-switch actif.
        """
        with self._lock:
            return self.live_trading and self.live_confirmed and not self.kill_switch


def load_exchanges() -> Dict[str, ExchangeConfig]:
    """
    Construit la table des exchanges supportés à partir de l'environnement.

    Convention des variables d'environnement (voir .env.example) :
        <EXCHANGE>_API_KEY, <EXCHANGE>_API_SECRET, <EXCHANGE>_API_PASSWORD,
        <EXCHANGE>_ENABLED
    """
    supported = ["cryptocom", "binance", "pionex", "bybit", "kraken"]
    exchanges: Dict[str, ExchangeConfig] = {}
    for name in supported:
        prefix = name.upper()
        exchanges[name] = ExchangeConfig(
            name=name,
            api_key=os.getenv(f"{prefix}_API_KEY", ""),
            api_secret=os.getenv(f"{prefix}_API_SECRET", ""),
            api_password=os.getenv(f"{prefix}_API_PASSWORD", ""),
            enabled=_env_bool(f"{prefix}_ENABLED", False),
            # Frais réels optionnels : renseignés une fois la plateforme connue.
            taker_fee=_env_float(f"{prefix}_TAKER_FEE", 0.0),
            maker_fee=_env_float(f"{prefix}_MAKER_FEE", 0.0),
            # Forfait sans frais par trade (abonnement illimité).
            flat_fee=_env_bool(f"{prefix}_FLAT_FEE", False),
        )
    return exchanges


# Instances globales partagées par toutes les applications.
# `settings` est modifiable en live ; `EXCHANGES` fournit les credentials.
settings = Settings()
EXCHANGES: Dict[str, ExchangeConfig] = load_exchanges()
