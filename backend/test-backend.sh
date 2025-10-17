#!/bin/bash
# Script de test de connectivité avec le backend

echo "🔍 Test de connectivité avec le backend..."

# Configuration
BACKEND_URL="${NEXT_PUBLIC_API_BASE_URL:-http://127.0.0.1:8000}"
echo "URL du backend: $BACKEND_URL"

# Test 1: Vérifier si le backend répond
echo "📡 Test 1: Connexion de base..."
if curl -s "$BACKEND_URL/" > /dev/null 2>&1; then
    echo "✅ Backend accessible"
else
    echo "❌ Backend non accessible"
    echo "   Vérifiez que le backend est démarré avec: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    exit 1
fi

# Test 2: Vérifier les endpoints d'authentification
echo "🔐 Test 2: Endpoints d'authentification..."
if curl -s "$BACKEND_URL/docs" > /dev/null 2>&1; then
    echo "✅ Documentation API accessible"
else
    echo "❌ Documentation API non accessible"
fi

# Test 3: Tester une requête d'authentification (devrait échouer avec 401)
echo "🚪 Test 3: Test d'authentification..."
response=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "401" ]; then
    echo "✅ Endpoint d'authentification fonctionne (401 attendu pour identifiants invalides)"
elif [ "$http_code" = "000" ]; then
    echo "❌ Impossible de contacter le backend (code 000)"
    echo "   Vérifiez l'URL: $BACKEND_URL"
else
    echo "⚠️  Réponse inattendue (code: $http_code)"
    echo "   Corps: $body"
fi

# Test 4: Vérifier CORS
echo "🌐 Test 4: Test CORS..."
cors_response=$(curl -s -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -X OPTIONS "$BACKEND_URL/auth/login")

if echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS configuré"
else
    echo "⚠️  CORS peut ne pas être configuré correctement"
fi

echo ""
echo "🎯 Si les tests échouent, vérifiez:"
echo "   1. Le backend est démarré"
echo "   2. L'URL NEXT_PUBLIC_API_BASE_URL est correcte"
echo "   3. Pas de problèmes de firewall/réseau"
echo "   4. Les logs du backend pour plus de détails"
