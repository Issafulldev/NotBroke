#!/bin/bash
# Script de déploiement rapide

echo "🚀 Déploiement NotBroke en cours..."

# Vérifier les prérequis
if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Générer une clé secrète si elle n'existe pas
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "🔑 Clé secrète générée: $SECRET_KEY"
fi

# Vérifier que les fichiers de configuration existent
echo "📋 Vérification des fichiers de configuration..."
if [ ! -f "backend/.env.example" ]; then
    echo "❌ backend/.env.example manquant"
    exit 1
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "❌ frontend/.env.local manquant"
    exit 1
fi

# Commit et push
echo "📦 Préparation du commit..."
git add .
git commit -m "Deploy: Update project"

echo "🚀 Push vers GitHub (déclenche le déploiement automatique)..."
git push origin main

echo "✅ Déploiement initié!"
echo "🔍 Surveillez le déploiement sur votre plateforme d'hébergement préférée"
echo "📝 N'oubliez pas de configurer les variables d'environnement!"
