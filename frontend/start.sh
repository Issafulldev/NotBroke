#!/bin/bash
# Script de démarrage pour Frontend Next.js

# Configuration des variables d'environnement
export NODE_ENV=production
export PORT=${PORT:-3000}

# Vérifier que les variables essentielles sont définies
if [ -z "$NEXT_PUBLIC_API_BASE_URL" ]; then
    echo "ERROR: NEXT_PUBLIC_API_BASE_URL environment variable must be set"
    exit 1
fi

# S'assurer que le dossier .next existe (build récent)
if [ ! -d ".next" ]; then
    echo "ERROR: Build directory .next not found. Please ensure build completed successfully."
    exit 1
fi

# Démarrer l'application Next.js
echo "Starting Next.js application..."
exec npm start
