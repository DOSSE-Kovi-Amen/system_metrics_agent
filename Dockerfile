# Dockerfile — environnement de production (multi-stage)
#
# Choix technique : une image unique partagée par les deux services
# (api et agent) du docker-compose.yaml. Les deux processus font partie
# de la même application et partagent le même code/dépendances ; seule
# la commande de démarrage diffère (uvicorn vs `python -m app.agent`),
# définie au niveau de chaque service dans docker-compose.yaml.
# Cela évite de dupliquer une image quasi identique et simplifie le
# pipeline CI/CD (un seul build/push).

# ---------- Étape 1 : build des dépendances ----------
FROM python:3.12-slim AS builder

WORKDIR /install

COPY requirements-prod.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements-prod.txt

# ---------- Étape 2 : image finale minimale ----------
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:${PATH}"

# Dépendances déjà compilées/installées, copiées depuis le builder
COPY --from=builder /install/deps /usr/local

# Outils système nécessaires (uptime pour la charge système)
RUN apt-get update && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

# Uniquement le code applicatif nécessaire à l'exécution (pas les tests,
# pas les fichiers de config du dépôt) — cf. .dockerignore
COPY app/ ./app/

# Utilisateur non-root dédié
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
    
USER appuser

EXPOSE 8000

# Healthcheck sur /health (réutilisé par docker-compose)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; \
sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else sys.exit(1)"]

# Commande par défaut : l'API. Le service "agent" du docker-compose.yaml
# écrase cette commande par ["python", "-m", "app.agent"].
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
