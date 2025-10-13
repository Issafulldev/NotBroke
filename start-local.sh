#!/bin/bash
# Script de démarrage pour le développement local

echo "🚀 Démarrage de l'application NotBroke en mode développement local..."

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Démarrer le backend
echo "🔧 Démarrage du backend..."
cd backend
source venv/bin/activate
echo "✅ Environnement virtuel activé"

# Vérifier les dépendances
echo "📦 Vérification des dépendances..."
pip list | grep -q sqlalchemy || {
    echo "Installation des dépendances..."
    pip install -r requirements.txt
}

# Démarrer le serveur backend
echo "🌐 Démarrage du serveur backend sur http://127.0.0.1:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "✅ Backend démarré (PID: $BACKEND_PID)"

# Attendre un peu pour que le backend démarre
sleep 3

# Vérifier que le backend répond
if curl -s http://127.0.0.1:8000/ > /dev/null; then
    echo "✅ Backend accessible"
else
    echo "❌ Backend non accessible - vérifiez les logs"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Démarrer le frontend
echo "🎨 Démarrage du frontend..."
cd ../frontend
if command -v npm &> /dev/null; then
    echo "📦 Démarrage avec npm..."
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend démarré (PID: $FRONTEND_PID)"
    echo "🌐 Frontend accessible sur http://localhost:3000"
else
    echo "❌ npm n'est pas installé"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 Application démarrée avec succès!"
echo "📋 URLs disponibles:"
echo "   🔗 Backend API: http://127.0.0.1:8000"
echo "   🔗 Documentation: http://127.0.0.1:8000/docs"
echo "   🌐 Frontend: http://localhost:3000"
echo ""
echo "🔐 Identifiants de connexion:"
echo "   👤 Username: admin"
echo "   🔑 Password: admin123"
echo ""
echo "⚠️  Pour arrêter: Ctrl+C (ou kill $BACKEND_PID $FRONTEND_PID)"

# Attendre les processus
wait $BACKEND_PID $FRONTEND_PID
