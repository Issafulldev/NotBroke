#!/bin/bash
# Script de déploiement pour Frontend Next.js

echo "🚀 Starting deployment process..."

# Installation des dépendances
echo "📦 Installing dependencies..."
npm install

# Build de l'application
echo "🔨 Building application..."
npm run build

# Vérification du build
if [ ! -d ".next" ]; then
    echo "❌ Build failed - .next directory not found"
    exit 1
fi

echo "✅ Build completed successfully"
echo "🎯 Ready for deployment"
