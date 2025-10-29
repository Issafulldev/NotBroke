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

# Exécuter les migrations Alembic avant de démarrer l'application
echo "🔄 Running database migrations..."
alembic upgrade head
MIGRATION_STATUS=$?
if [ $MIGRATION_STATUS -ne 0 ]; then
    echo "❌ Migration failed! Exit code: $MIGRATION_STATUS"
    echo "📋 Attempting to diagnose the issue..."
    echo "💡 You can try running manually: python3 migrate_currency.py"
    echo "⚠️  Continuing startup anyway - application may fail if migrations are incomplete"
    # Ne pas arrêter l'app pour permettre le diagnostic manuel
    # exit 1
else
    echo "✅ Migrations completed successfully"
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
