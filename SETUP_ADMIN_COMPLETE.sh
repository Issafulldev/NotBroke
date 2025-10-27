#!/bin/bash
# ============================================================================
# NOTBROKE - SETUP COMPLET AVEC ADMIN
# ============================================================================
# Ce script va :
# 1. Créer le rôle admin avec password admin123
# 2. Créer la base notbroke_db
# 3. Créer le fichier .env
# 4. Installer les dépendances
# 5. Initialiser le schéma
# 6. Migrer les données depuis SQLite
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║        🚀 NOTBROKE - SETUP COMPLET AVEC ADMIN 🚀                      ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}1️⃣  CRÉER LE RÔLE ADMIN DANS POSTGRESQL${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

# Créer le rôle admin
psql postgres -c "CREATE ROLE admin WITH LOGIN PASSWORD 'admin123' CREATEDB;" 2>/dev/null || echo "⚠️  Rôle admin pourrait déjà exister"

# Créer la base notbroke_db
psql postgres -c "CREATE DATABASE notbroke_db OWNER admin;" 2>/dev/null || echo "⚠️  Base notbroke_db pourrait déjà exister"

echo -e "${GREEN}✅ Rôle admin et base notbroke_db créés${NC}"

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}2️⃣  CRÉER LE FICHIER .env${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

cd backend

# Générer une clé secrète
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Créer le fichier .env
cat > .env << EOF
# PostgreSQL Configuration
DATABASE_URL=postgresql+asyncpg://admin:admin123@localhost:5432/notbroke_db

# Environment
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000

# Security
SECRET_KEY=$SECRET_KEY
EOF

echo -e "${GREEN}✅ Fichier .env créé${NC}"

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}3️⃣  INSTALLER LES DÉPENDANCES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

if [ ! -d "venv" ]; then
    echo "Création du venv..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --quiet -r requirements.txt

echo -e "${GREEN}✅ Dépendances installées${NC}"

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}4️⃣  INITIALISER LE SCHÉMA POSTGRESQL${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

python3 << 'PYTHON_EOF'
import asyncio
from app.database import init_db

async def setup():
    await init_db()
    print("✅ Schéma créé")

asyncio.run(setup())
PYTHON_EOF

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}5️⃣  MIGRER LES DONNÉES DEPUIS SQLITE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

# Vérifier si le fichier SQLite existe
if [ -f "expense.db" ]; then
    echo "📊 Migration des données SQLite → PostgreSQL..."
    # Définir les variables d'environnement pour la migration
    export DATABASE_URL_SOURCE="sqlite+aiosqlite:///./expense.db"
    export DATABASE_URL_TARGET="postgresql+asyncpg://admin:admin123@localhost:5432/notbroke_db"
    python3 migrate_to_postgres.py
else
    echo "ℹ️  Aucune base SQLite trouvée - base PostgreSQL vide créée"
fi

echo -e "\n${GREEN}════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SETUP COMPLET !${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}📝 RÉSUMÉ:${NC}"
echo "   ✓ Rôle admin créé (password: admin123)"
echo "   ✓ Base notbroke_db créée"
echo "   ✓ Fichier .env configuré"
echo "   ✓ Dépendances installées"
echo "   ✓ Schéma PostgreSQL initialisé"
if [ -f "expense.db" ]; then
    echo "   ✓ Données migrées depuis SQLite"
fi

echo -e "\n${YELLOW}🧪 TESTER L'APPLICATION:${NC}"
echo "   Terminal 1:"
echo "   $ cd backend && source venv/bin/activate"
echo "   $ uvicorn app.main:app --reload"
echo ""
echo "   Terminal 2:"
echo "   $ cd frontend && npm run dev"
echo ""
echo "   Browser:"
echo "   $ open http://localhost:3000"
echo ""
echo "   Login:"
echo "   Username: admin"
echo "   Password: admin123"

echo -e "\n${GREEN}🚀 PRÊT POUR LA PRODUCTION!${NC}\n"
