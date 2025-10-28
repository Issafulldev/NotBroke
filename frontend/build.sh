#!/bin/bash
set -e

# Force le répertoire courant au répertoire du projet
cd "$(dirname "$(pwd)")" 2>/dev/null || cd /

# Chercher le répertoire frontend
if [ -d "frontend" ]; then
    cd frontend
elif [ -d "../frontend" ]; then
    cd ../frontend
elif [ -d "../../frontend" ]; then
    cd ../../frontend
fi

echo "📁 Working directory: $(pwd)"
echo "📦 Installing dependencies..."
npm install

echo "🔨 Building..."
npm run build

echo "✅ Build successful!"
