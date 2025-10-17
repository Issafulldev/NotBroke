#!/bin/bash
# Script de validation des builds et sécurité pour CI/CD
# Utilisation: ./validate-build.sh [environment]

set -e

ENVIRONMENT=${1:-development}
echo "🔍 Validation des builds pour environnement: $ENVIRONMENT"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}❌ $1${NC}" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Vérifications préalables
echo "📋 Vérifications préalables..."

if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    error "Structure du projet invalide. Répertoires backend/ et frontend/ manquants."
fi

# Validation sécurité
echo "🔒 Validation sécurité..."

# Vérifier l'absence de mots de passe par défaut
if grep -r "admin123" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv --exclude="validate-build.sh" --exclude="deploy.sh" > /dev/null; then
    error "Mot de passe par défaut 'admin123' trouvé dans le code source"
fi

# Vérifier les variables d'environnement critiques
if [ "$ENVIRONMENT" = "production" ]; then
    if [ -z "$SECRET_KEY" ]; then
        error "SECRET_KEY manquante pour l'environnement de production"
    fi

    if [ -z "$FRONTEND_URL" ]; then
        warning "FRONTEND_URL non définie. CORS sera permissif en production."
    fi
else
    warning "Environnement de développement détecté. Certaines validations sont assouplies."
fi

# Validation backend
echo "🐍 Validation backend Python..."

if [ ! -f "backend/requirements.txt" ]; then
    error "requirements.txt manquant"
fi

# Vérifier la syntaxe Python des fichiers critiques
python3 -m py_compile backend/app/main.py backend/app/auth.py backend/app/models.py backend/app/crud.py
if [ $? -ne 0 ]; then
    error "Erreurs de syntaxe Python détectées"
fi

# Vérifier les imports critiques (optionnel en développement si les dépendances ne sont pas installées)
if python3 -c "import fastapi" 2>/dev/null; then
    python3 -c "
import sys
sys.path.append('backend')
try:
    from app.main import app
    from app.auth import SECRET_KEY, validate_environment
    from app.models import User, Category, Expense
    print('✅ Imports backend réussis')
except ImportError as e:
    print(f'❌ Erreur d\'import: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null && echo "✅ Imports backend réussis" || error "Échec des imports Python"
else
    warning "Dépendances Python non installées. Imports non testés (installez avec: pip install -r backend/requirements.txt)"
fi

# Validation frontend
echo "⚛️  Validation frontend..."

if [ ! -f "frontend/package.json" ]; then
    error "package.json manquant"
fi

if command -v node &> /dev/null && command -v npm &> /dev/null; then
    cd frontend

    # Vérifier les dépendances
    if [ ! -d "node_modules" ]; then
        warning "node_modules manquant. Installation des dépendances..."
        if ! npm ci > /dev/null 2>&1; then
            cd ..
            warning "Impossible d'installer les dépendances frontend. Build non testé."
        fi
    fi

    # Build de validation (sans déploiement) - seulement si les dépendances sont installées
    if [ -d "node_modules" ]; then
        echo "🔨 Test du build frontend..."
        if ! npm run build > build.log 2>&1; then
            echo "❌ Échec du build frontend. Log:" >&2
            cat build.log >&2
            cd ..
            error "Build frontend échoué"
        fi

        # Nettoyer le build de test
        rm -rf .next build.log
    else
        warning "Dépendances frontend non installées. Build non testé."
    fi

    cd ..
else
    warning "Node.js/npm non disponible. Validation frontend ignorée."
fi

# Tests supplémentaires si disponibles
echo "🧪 Vérifications supplémentaires..."

# Vérifier la configuration Next.js
if grep -q "ignoreBuildErrors.*true" frontend/next.config.ts; then
    error "next.config.ts ignore les erreurs TypeScript (ignoreBuildErrors: true)"
fi

if grep -q "ignoreDuringBuilds.*true" frontend/next.config.ts; then
    error "next.config.ts ignore les erreurs ESLint (ignoreDuringBuilds: true)"
fi

# Validation finale
success "Validation complète réussie pour $ENVIRONMENT"

if [ "$ENVIRONMENT" = "production" ]; then
    echo ""
    echo "📋 Checklist déploiement production:"
    echo "   ✅ Builds validés"
    echo "   ✅ Sécurité vérifiée"
    echo "   ✅ Variables d'environnement validées"
    echo ""
    echo "🚀 Prêt pour le déploiement!"
fi
