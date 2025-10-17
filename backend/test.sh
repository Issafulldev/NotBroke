#!/bin/bash
# Script pour exécuter les tests du backend

set -e

echo "🧪 Exécution des tests backend..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "requirements.txt" ]; then
    echo "❌ Fichier requirements.txt non trouvé. Êtes-vous dans le répertoire backend ?"
    exit 1
fi

# Installer les dépendances si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "🧪 Exécution des tests..."
python -m pytest --tb=short --cov=app --cov-report=term-missing

echo "✅ Tests terminés!"
