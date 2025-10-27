#!/bin/bash
# Setup PostgreSQL pour le développement local
# Supporte macOS (Homebrew) et Linux (apt)

set -e

echo "🐘 Configuration PostgreSQL pour NotBroke"
echo "=========================================="

# Déterminer le système d'exploitation
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "❌ Système d'exploitation non supporté: $OSTYPE"
    exit 1
fi

echo "Système détecté: $OS"

# Installation PostgreSQL
if [ "$OS" = "macos" ]; then
    echo "\n1️⃣  Vérification de Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew non trouvé. Installez-le depuis https://brew.sh"
        exit 1
    fi
    
    echo "✅ Homebrew trouvé"
    
    echo "\n2️⃣  Installation de PostgreSQL..."
    if brew list postgresql@15 &> /dev/null; then
        echo "✅ PostgreSQL@15 déjà installé"
    else
        brew install postgresql@15
        echo "✅ PostgreSQL@15 installé"
    fi
    
    echo "\n3️⃣  Démarrage de PostgreSQL..."
    brew services start postgresql@15 || true
    echo "✅ PostgreSQL démarré"
    
    # Attendre que PostgreSQL soit prêt
    sleep 2

elif [ "$OS" = "linux" ]; then
    echo "\n1️⃣  Vérification des droits sudo..."
    if ! sudo -n true 2>/dev/null; then
        echo "⚠️  Ce script a besoin des droits sudo"
        echo "Veuillez entrer votre mot de passe:"
    fi
    
    echo "\n2️⃣  Mise à jour des paquets..."
    sudo apt update
    
    echo "\n3️⃣  Installation de PostgreSQL..."
    sudo apt install -y postgresql postgresql-contrib
    echo "✅ PostgreSQL installé"
    
    echo "\n4️⃣  Démarrage de PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    echo "✅ PostgreSQL démarré et activé au démarrage"
fi

# Créer la base de données et l'utilisateur
echo "\n5️⃣  Création de la base de données et de l'utilisateur..."

# Vérifier si l'utilisateur existe déjà
if [ "$OS" = "macos" ]; then
    if psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw notbroke_db; then
        echo "⚠️  Base de données 'notbroke_db' existe déjà"
        read -p "Voulez-vous la recréer? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            psql -U postgres -c "DROP DATABASE IF EXISTS notbroke_db;"
            psql -U postgres -c "DROP USER IF EXISTS notbroke_user;"
        else
            echo "✅ Base de données conservée"
            exit 0
        fi
    fi
    
    echo "Création de l'utilisateur et de la base..."
    psql -U postgres -c "CREATE USER notbroke_user WITH PASSWORD 'notbroke_password';"
    psql -U postgres -c "CREATE DATABASE notbroke_db OWNER notbroke_user;"
    psql -U postgres -c "ALTER USER notbroke_user CREATEDB;"
    
elif [ "$OS" = "linux" ]; then
    if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw notbroke_db; then
        echo "⚠️  Base de données 'notbroke_db' existe déjà"
        read -p "Voulez-vous la recréer? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo -u postgres psql -c "DROP DATABASE IF EXISTS notbroke_db;"
            sudo -u postgres psql -c "DROP USER IF EXISTS notbroke_user;"
        else
            echo "✅ Base de données conservée"
            exit 0
        fi
    fi
    
    echo "Création de l'utilisateur et de la base..."
    sudo -u postgres psql -c "CREATE USER notbroke_user WITH PASSWORD 'notbroke_password';"
    sudo -u postgres psql -c "CREATE DATABASE notbroke_db OWNER notbroke_user;"
    sudo -u postgres psql -c "ALTER USER notbroke_user CREATEDB;"
fi

echo "✅ Utilisateur 'notbroke_user' créé"
echo "✅ Base de données 'notbroke_db' créée"

# Créer le fichier .env
echo "\n6️⃣  Configuration du fichier .env..."

if [ -f ".env" ]; then
    echo "⚠️  Fichier .env existe déjà"
    read -p "Voulez-vous le mettre à jour? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

cat > .env << 'EOF'
# PostgreSQL (Development)
DATABASE_URL=postgresql+asyncpg://notbroke_user:notbroke_password@localhost:5432/notbroke_db

# Environment
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000

# Security (change this in production!)
SECRET_KEY=dev_secret_key_change_in_production
EOF

echo "✅ Fichier .env créé"

echo "\n=========================================="
echo "✅ Configuration terminée!"
echo "\n📝 Prochaines étapes:"
echo "  1. cd backend && source venv/bin/activate"
echo "  2. pip install -r requirements.txt"
echo "  3. uvicorn app.main:app --reload"
echo "\n💡 Credentials PostgreSQL:"
echo "  Username: notbroke_user"
echo "  Password: notbroke_password"
echo "  Database: notbroke_db"
echo "  Host: localhost"
echo "\n⚠️  ATTENTION: Changez le mot de passe en production!"
