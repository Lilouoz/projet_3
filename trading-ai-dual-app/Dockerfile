# ============================================================================
# Dockerfile — image commune pour trading-ai-dual-app
# Basée sur l'image officielle Freqtrade (embarque déjà TA-Lib + Python),
# ce qui évite la compilation laborieuse de TA-Lib (règle : ne pas réécrire
# le moteur de backtest, réutiliser Freqtrade).
# ============================================================================
FROM freqtradeorg/freqtrade:stable

# On repasse en root pour installer les dépendances applicatives.
USER root

WORKDIR /app

# Copie et installation des dépendances Python additionnelles.
# (Freqtrade est déjà présent dans l'image de base ; pip ignorera le doublon.)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copie du code source.
COPY . /app

# PYTHONPATH pour résoudre les imports `core`, `strategies`, etc. et les
# modules internes des apps (main.py, analyzer.py…).
ENV PYTHONPATH=/app:/app/app-swing:/app/app-scalp:/app/auto-update:/app/dashboard

# Port du dashboard FastAPI.
EXPOSE 8000

# Commande par défaut : le dashboard. Les autres services surchargent
# `command:` dans docker-compose.yml.
CMD ["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"]
