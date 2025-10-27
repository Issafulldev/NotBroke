#!/bin/bash
# ============================================================================
# NOTBROKE - MIGRATION POSTGRESQL - SCRIPT FINAL
# ============================================================================
# Ce script finalise la migration de SQLite vers PostgreSQL
# Usage: ./MIGRATION_FINAL.sh
# ============================================================================

set -e

clear
cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              🚀 NOTBROKE - MIGRATION POSTGRESQL - DÉMARRAGE 🚀             ║
║                                                                            ║
║                        Suivez les étapes ci-dessous                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

EOF

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 VÉRIFICATION PRÉALABLE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"

# 1. Vérifier Python
echo -e "\n${YELLOW}1️⃣  Vérification de Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} trouvé${NC}"
else
    echo -e "${RED}✗ Python3 non trouvé${NC}"
    exit 1
fi

# 2. Vérifier le venv
echo -e "\n${YELLOW}2️⃣  Vérification du venv...${NC}"
if [ -d "backend/venv" ]; then
    echo -e "${GREEN}✓ Venv trouvé${NC}"
else
    echo -e "${RED}✗ Venv non trouvé. Création...${NC}"
    cd backend
    python3 -m venv venv
    cd ..
    echo -e "${GREEN}✓ Venv créé${NC}"
fi

# 3. Vérifier les fichiers requis
echo -e "\n${YELLOW}3️⃣  Vérification des fichiers...${NC}"
FILES=(
    "backend/requirements.txt"
    "backend/migrate_to_postgres.py"
    "backend/setup-postgres.sh"
    "POSTGRESQL_SETUP_GUIDE.md"
    "MIGRATION_POSTGRESQL.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file manquant${NC}"
        exit 1
    fi
done

echo -e "\n${GREEN}✅ Toutes les vérifications réussies!${NC}"

# 4. Afficher les options
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🎯 CHOISISSEZ VOTRE SCÉNARIO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"

cat << 'EOF'

1️⃣  SETUP AUTOMATISÉ (Recommandé)
   ✓ Installe PostgreSQL (si nécessaire)
   ✓ Crée la base de données
   ✓ Configure les fichiers .env
   ⏱️  Durée: ~10 minutes
   📝 Commande: ./setup-postgres.sh

2️⃣  MIGRER LES DONNÉES
   ✓ Migre SQLite → PostgreSQL
   ✓ Valide les données
   ✓ Affiche un rapport
   ⏱️  Durée: ~5 minutes
   📝 Commande: python migrate_to_postgres.py

3️⃣  GUIDE COMPLET
   ✓ Instructions détaillées
   ✓ Troubleshooting
   ✓ Déploiement (Render/VPS)
   📖 Fichier: POSTGRESQL_SETUP_GUIDE.md

4️⃣  DOCUMENTION COMPLÈTE
   ✓ Vue d'ensemble technique
   ✓ Tous les scénarios couverts
   📖 Fichier: POSTGRESQL_INDEX.md

0️⃣  QUITTER

EOF

read -p "Votre choix (0-4): " choice

case $choice in
    1)
        echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}🔧 EXÉCUTION DU SETUP AUTOMATISÉ${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        cd backend
        chmod +x setup-postgres.sh
        ./setup-postgres.sh
        ;;
    
    2)
        echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}📊 MIGRATION DES DONNÉES${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        
        source backend/venv/bin/activate
        cd backend
        python migrate_to_postgres.py
        ;;
    
    3)
        echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}📖 OUVERTURE DU GUIDE D'INSTALLATION${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        
        if command -v open &> /dev/null; then
            open POSTGRESQL_SETUP_GUIDE.md
        elif command -v xdg-open &> /dev/null; then
            xdg-open POSTGRESQL_SETUP_GUIDE.md
        else
            cat POSTGRESQL_SETUP_GUIDE.md
        fi
        ;;
    
    4)
        echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}📖 OUVERTURE DE LA DOCUMENTATION COMPLÈTE${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
        
        if command -v open &> /dev/null; then
            open POSTGRESQL_INDEX.md
        elif command -v xdg-open &> /dev/null; then
            xdg-open POSTGRESQL_INDEX.md
        else
            cat POSTGRESQL_INDEX.md
        fi
        ;;
    
    0)
        echo -e "\n${YELLOW}Au revoir! 👋${NC}"
        exit 0
        ;;
    
    *)
        echo -e "\n${RED}❌ Choix invalide${NC}"
        exit 1
        ;;
esac

# Afficher le résumé final
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ÉTAPE COMPLÉTÉE!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"

cat << 'EOF'

📝 PROCHAINES ÉTAPES:

1. Vérifiez que tout fonctionne:
   $ uvicorn app.main:app --reload  (Backend)
   $ npm run dev                      (Frontend)

2. Testez l'application:
   - Ouvrez http://localhost:3000
   - Testez la connexion/inscription
   - Créez une catégorie
   - Ajoutez une dépense
   - Exportez les données

3. Si tout fonctionne:
   $ git add .
   $ git commit -m "feat: PostgreSQL migration complete"
   $ git push

4. Déployez sur Render/VPS:
   → Voir MIGRATION_POSTGRESQL.md

✨ Vous êtes prêt pour la production! 🚀

EOF

echo ""
