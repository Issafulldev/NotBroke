# Guide de Migration de Base de Données sur Render

Ce guide explique comment appliquer les migrations Alembic sur votre base de données PostgreSQL hébergée sur Render.

## 📋 Vue d'ensemble

**Les migrations s'exécutent maintenant automatiquement** au démarrage du serveur grâce au script `start.sh` modifié. Cependant, si vous souhaitez exécuter manuellement les migrations ou vérifier leur statut, ce guide vous aidera.

## 🔄 Migration Automatique (Recommandé)

### Option 1 : Via le script de démarrage (Automatique)

Le script `start.sh` a été modifié pour exécuter automatiquement les migrations Alembic avant de démarrer l'application :

```bash
# Les migrations s'exécutent automatiquement lors du déploiement
alembic upgrade head
```

**Cela signifie que chaque fois que vous déployez votre code sur Render, les migrations seront appliquées automatiquement.**

## 🛠️ Migration Manuelle (Si nécessaire)

Si vous devez exécuter les migrations manuellement (par exemple pour vérifier l'état ou en cas d'erreur), voici comment procéder :

### Prérequis

1. Accédez à votre dashboard Render
2. Notez les informations de connexion PostgreSQL :
   - Host
   - Port
   - Database name
   - Username
   - Password (trouvable dans l'onglet "Connections" de votre base de données)

### Option A : Via Render Shell (Recommandé)

1. **Accédez à votre service backend sur Render**
2. **Ouvrez le Shell** (bouton "Shell" dans le dashboard Render)
3. **Exécutez les commandes suivantes** :

```bash
# Activer l'environnement virtuel (si nécessaire)
source venv/bin/activate  # ou python -m venv venv && source venv/bin/activate

# Vérifier l'état actuel des migrations
alembic current

# Appliquer toutes les migrations en attente
alembic upgrade head

# Vérifier que la colonne currency existe
python3 -c "
import asyncio
from app.database import get_session
from app.models import Expense
from sqlalchemy import select, text

async def check():
    async for session in get_session():
        result = await session.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='expenses' AND column_name='currency'\"))
        row = result.first()
        if row:
            print('✅ Colonne currency existe')
        else:
            print('❌ Colonne currency n\\'existe pas')
        break

asyncio.run(check())
"
```

### Option B : Via psql directement

1. **Depuis votre machine locale** (avec accès SSH ou VPN vers Render) :

```bash
# Installer psql si nécessaire (macOS: brew install postgresql)
PGPASSWORD=<votre_password> psql -h <host_render> -U <username> -d <database_name> -c "\d expenses"
```

2. **Ou utilisez l'onglet "Connections" de Render** qui vous donne une commande psql prête à copier

### Option C : Via un script Python (Render Shell)

1. **Ouvrez le Shell Render**
2. **Créez un script temporaire** :

```bash
cat > migrate_check.py << 'EOF'
import asyncio
from alembic import command
from alembic.config import Config

# Charger la configuration Alembic
alembic_cfg = Config("alembic.ini")

# Exécuter les migrations
command.upgrade(alembic_cfg, "head")
print("✅ Migrations appliquées avec succès")
EOF

python3 migrate_check.py
```

## 🔍 Vérification de l'état des migrations

### Vérifier la version actuelle

```bash
alembic current
```

### Vérifier l'historique des migrations

```bash
alembic history
```

### Vérifier que la colonne currency existe

```bash
# Dans Render Shell
python3 << 'EOF'
import asyncio
from app.database import get_session
from sqlalchemy import text

async def check():
    async for session in get_session():
        result = await session.execute(
            text("SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='expenses' AND column_name='currency'")
        )
        row = result.first()
        if row:
            print(f"✅ Colonne currency existe: {row}")
        else:
            print("❌ Colonne currency n'existe pas")
        break

asyncio.run(check())
EOF
```

## 🚨 En cas de problème

### Problème : Migration échoue avec "column already exists"

Cela signifie que la colonne existe déjà. C'est normal si vous avez déjà exécuté la migration manuellement.

### Problème : "No such file or directory: alembic"

Assurez-vous d'être dans le répertoire `backend/` du projet.

### Problème : "Module 'app' not found"

Vérifiez que vous êtes dans le bon répertoire et que toutes les dépendances sont installées :
```bash
pip install -r requirements.txt
```

### Problème : Connexion à la base de données échoue

1. Vérifiez que la variable d'environnement `DATABASE_URL` est correctement configurée dans Render
2. Vérifiez que votre IP est autorisée dans les paramètres de sécurité PostgreSQL de Render
3. Vérifiez les logs de Render pour plus de détails

## 📝 Variables d'environnement nécessaires

Assurez-vous que ces variables sont configurées dans Render :

- `DATABASE_URL` : URL de connexion PostgreSQL (ex: `postgresql+asyncpg://user:pass@host:port/dbname`)
- `ENVIRONMENT` : `production`
- `SECRET_KEY` : Clé secrète pour JWT
- `FRONTEND_URL` : URL de votre frontend

## 🚨 Problème : Erreur 500 sur /categories et /expenses

Si vous rencontrez des erreurs 500 sur les endpoints `/categories` et `/expenses` après le déploiement, c'est probablement que la migration n'a pas été appliquée.

### Solution rapide via Render Shell

1. **Ouvrez le Shell Render** de votre service backend
2. **Exécutez la migration manuellement** :

```bash
cd backend  # Si nécessaire
source venv/bin/activate  # Si nécessaire
python3 migrate_currency.py
```

Ou directement avec Alembic :

```bash
cd backend  # Si nécessaire
source venv/bin/activate  # Si nécessaire
alembic upgrade head
```

### Vérifier les logs Render

Dans le dashboard Render, consultez les logs du service backend. Vous devriez voir :

- ✅ Si la migration a réussi : `✅ Migrations completed successfully`
- ❌ Si la migration a échoué : `❌ Migration failed! Exit code: X`

### Diagnostic avancé

Si la migration échoue, exécutez ce script de diagnostic dans Render Shell :

```bash
python3 << 'EOF'
import asyncio
from app.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        # Vérifier si la colonne existe
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='expenses' AND column_name='currency'")
        )
        row = result.first()
        if row:
            print('✅ Colonne currency existe')
        else:
            print('❌ Colonne currency n\'existe pas')
            print('💡 Exécutez: python3 migrate_currency.py')
        
        # Vérifier la version Alembic
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.first()
            if version:
                print(f'📋 Version Alembic actuelle: {version[0]}')
        except Exception as e:
            print(f'⚠️  Impossible de lire la version Alembic: {e}')

asyncio.run(check())
EOF
```

## ✅ Après la migration

1. **Vérifiez les logs** du service backend sur Render pour confirmer que les migrations ont réussi
2. **Testez l'application** en créant une nouvelle dépense avec différentes devises
3. **Vérifiez que les anciennes dépenses** ont bien la devise EUR par défaut

## 🔗 Ressources utiles

- [Documentation Render - PostgreSQL](https://render.com/docs/databases)
- [Documentation Alembic](https://alembic.sqlalchemy.org/)
- [Guide de migration Alembic du projet](./ALEMBIC_GUIDE.md)

