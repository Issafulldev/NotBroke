#!/bin/bash
# Script de déploiement sécurisé avec validation

set -e  # Arrêter le script en cas d'erreur

echo "🚀 Déploiement NotBroke avec validation de sécurité..."

# Fonction de validation
validate_deployment() {
    echo "🔍 Validation du déploiement..."

    # Vérifier les prérequis
    if ! command -v git &> /dev/null; then
        echo "❌ Git n'est pas installé"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 n'est pas installé"
        exit 1
    fi

    # Vérifier l'état du dépôt git
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  Le dépôt git contient des changements non committés"
        echo "   Committez vos changements avant le déploiement"
        exit 1
    fi

    # Validation des builds
    echo "🔨 Validation des builds..."

    # Backend: vérifier la syntaxe Python
    echo "   Vérification Python..."
    python3 -m py_compile backend/app/main.py backend/app/auth.py backend/app/models.py
    if [ $? -ne 0 ]; then
        echo "❌ Erreurs de syntaxe Python détectées"
        exit 1
    fi

    # Frontend: vérifier le build
    if command -v npm &> /dev/null; then
        echo "   Vérification du build frontend..."
        cd frontend
        if ! npm run build > /dev/null 2>&1; then
            echo "❌ Échec du build frontend"
            echo "   Corrigez les erreurs TypeScript/ESLint avant le déploiement"
            cd ..
            exit 1
        fi
        cd ..
    fi

    # Validation de sécurité
    echo "🔒 Validation de sécurité..."

    # Vérifier qu'aucun mot de passe par défaut n'est présent
    if grep -r "admin123" . --exclude-dir=.git --exclude-dir=node_modules --exclude="validate-build.sh" --exclude="deploy.sh" > /dev/null; then
        echo "❌ Mot de passe par défaut 'admin123' trouvé dans le code"
        exit 1
    fi

    # Vérifier les variables d'environnement critiques
    if [ -z "$SECRET_KEY" ] && [ "$ENVIRONMENT" = "production" ]; then
        echo "❌ SECRET_KEY manquante pour l'environnement de production"
        echo "   Définissez SECRET_KEY avant le déploiement"
        exit 1
    fi

    echo "✅ Validation réussie"
}

# Générer une clé secrète si nécessaire (seulement pour développement)
if [ -z "$SECRET_KEY" ] && [ "$ENVIRONMENT" != "production" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "🔑 Clé secrète générée pour développement: $SECRET_KEY"
    echo "   ⚠️  N'utilisez PAS cette clé en production!"
fi

# Exécuter la validation
validate_deployment

# Commit et push
echo "📦 Préparation du commit..."
git add .

# Vérifier s'il y a des changements à committer
if git diff --cached --quiet; then
    echo "ℹ️  Aucun changement à committer"
else
    git commit -m "Deploy: $(date +'%Y-%m-%d %H:%M:%S') - Phase 1 security improvements"
fi

echo "🚀 Push vers GitHub (déclenche le déploiement automatique)..."
git push origin main

echo "✅ Déploiement validé et initié!"
echo "🔍 Surveillez le déploiement sur votre plateforme d'hébergement"
echo "📝 Variables d'environnement à configurer en production:"
echo "   - SECRET_KEY (obligatoire)"
echo "   - FRONTEND_URL (recommandé)"
echo "   - ENVIRONMENT=production"
