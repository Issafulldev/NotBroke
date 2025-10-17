#!/bin/bash
# Script de démarrage pour l'application backend

# Optimisations de performance
export PYTHONOPTIMIZE=1
export PYTHONUNBUFFERED=1

# Créer le répertoire si nécessaire
mkdir -p /app

# Vérifier que la SECRET_KEY est définie en production
if [ "$ENVIRONMENT" = "production" ] && [ -z "$SECRET_KEY" ]; then
    echo "ERROR: SECRET_KEY environment variable must be set in production"
    exit 1
fi

# Lancer l'application avec des optimisations pour le plan gratuit
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --no-access-log \
    --log-level warning
