# 🚀 Guide de migration SQLite → PostgreSQL

Ce guide couvre la migration de votre application NotBroke de SQLite vers PostgreSQL.

## 📋 Table des matières

1. [Migration en développement local](#migration-en-développement-local)
2. [Déploiement sur VPS Hostinger](#déploiement-sur-vps-hostinger)
3. [Déploiement sur Render](#déploiement-sur-render)
4. [Troubleshooting](#troubleshooting)

---

## 🔄 Migration en développement local

### Prérequis

```bash
# Assurez-vous que PostgreSQL est installé
# macOS
brew install postgresql@15
brew services start postgresql@15

# Linux
sudo apt install postgresql postgresql-contrib

# Windows
# Télécharger de https://www.postgresql.org/download/windows/
```

### Étape 1 : Installer les dépendances Python

```bash
cd backend
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
# asyncpg devrait être installé automatiquement
```

### Étape 2 : Créer une base de données PostgreSQL

```bash
# Connectez-vous à PostgreSQL
psql postgres

# Créer la base et l'utilisateur
CREATE USER notbroke_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE notbroke_db OWNER notbroke_user;

# Vérifier
\l  # Lister les bases
\q  # Quitter
```

### Étape 3 : Configurer les variables d'environnement

**Créer ou modifier `.env`** dans le dossier `backend/` :

```bash
# SQLite (ancien)
# DATABASE_URL=sqlite+aiosqlite:///./expense.db

# PostgreSQL (nouveau)
DATABASE_URL=postgresql+asyncpg://notbroke_user:your_secure_password@localhost:5432/notbroke_db
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
SECRET_KEY=your_development_secret_key
```

### Étape 4 : Migrer les données (si vous avez des données en SQLite)

```bash
# Depuis le dossier backend/
python migrate_to_postgres.py
```

**Résultat attendu** :
```
======================================================================
🚀 MIGRATION SQLite → PostgreSQL
======================================================================
Source: sqlite+aiosqlite:///./expense.db
Target: postgresql+asyncpg://notbroke_user:password@localhost:5432/notbroke_db
======================================================================

🔌 Connexion aux bases de données...
  ✅ SQLite connecté
  ✅ PostgreSQL connecté

📋 Création du schéma PostgreSQL...
  ✅ Schéma créé

👥 Migration des utilisateurs...
  ✅ 2 utilisateur(s) migré(s)

📂 Migration des catégories...
  ✅ 5 catégorie(s) migrée(s)

💰 Migration des dépenses...
  ✅ 23 dépense(s) migrée(s)

🌐 Migration des traductions...
  ✅ 143 traduction(s) migrée(s)

======================================================================
📋 RÉSUMÉ DE LA MIGRATION
======================================================================
Utilisateurs:         2
Catégories:           5
Dépenses:            23
Traductions:        143
======================================================================

✅ Migration réussie!

📝 Prochaines étapes:
  1. Mettre à jour DATABASE_URL dans votre .env
  2. Tester l'application
  3. Déployer sur Render/VPS
```

### Étape 5 : Tester l'application

```bash
# Terminal 1 : Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 : Frontend
cd frontend
npm run dev

# Vérifier que l'app fonctionne normalement
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
```

**Points de vérification** :
- ✅ Connexion/Inscription fonctionne
- ✅ Créer une catégorie fonctionne
- ✅ Ajouter une dépense fonctionne
- ✅ Voir les données fonctionne
- ✅ Exporter en CSV/XLSX fonctionne

---

## 🏗️ Déploiement sur VPS Hostinger

### Prérequis

- VPS avec SSH accès
- Python 3.13
- PostgreSQL installé

### Étape 1 : Préparation du VPS

```bash
ssh root@votre_ip_vps

# Mise à jour
apt update && apt upgrade -y

# Installation PostgreSQL
apt install -y postgresql postgresql-contrib

# Démarrer PostgreSQL
systemctl start postgresql
systemctl enable postgresql
```

### Étape 2 : Créer la base de données

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Commandes PostgreSQL
CREATE USER notbroke_user WITH PASSWORD 'your_very_secure_password';
CREATE DATABASE notbroke_db OWNER notbroke_user;

# Vérifier les connexions
ALTER ROLE notbroke_user CREATEDB;

\q
```

### Étape 3 : Configurer PostgreSQL pour accepter les connexions

Modifier `/etc/postgresql/15/main/postgresql.conf` :

```bash
# Trouver et modifier :
# listen_addresses = 'localhost'  # si local uniquement
# OU pour accepter externes:
listen_addresses = '*'
```

Modifier `/etc/postgresql/15/main/pg_hba.conf` :

```bash
# Ajouter à la fin :
host    notbroke_db    notbroke_user    127.0.0.1/32    md5
host    notbroke_db    notbroke_user    ::1/128         md5
```

Redémarrer PostgreSQL :

```bash
sudo systemctl restart postgresql
```

### Étape 4 : Déployer l'application

```bash
cd /home
git clone https://github.com/votre-username/NotBroke.git
cd NotBroke/backend

# Créer venv et installer
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configuration .env
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://notbroke_user:your_very_secure_password@localhost:5432/notbroke_db
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENVIRONMENT=production
FRONTEND_URL=https://votre-domaine.com
EOF

# Initialiser la base de données
python3 -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Étape 5 : Configuration des services systemd

Créer `/etc/systemd/system/notbroke-backend.service` :

```ini
[Unit]
Description=NotBroke Backend
After=network.target postgresql.service

[Service]
Type=notify
User=notbroke
WorkingDirectory=/home/NotBroke/backend
Environment="PATH=/home/NotBroke/backend/venv/bin"
ExecStart=/home/NotBroke/backend/venv/bin/gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level warning

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Créer `/etc/systemd/system/notbroke-frontend.service` :

```ini
[Unit]
Description=NotBroke Frontend
After=network.target

[Service]
Type=simple
User=notbroke
WorkingDirectory=/home/NotBroke/frontend
ExecStart=/usr/bin/node /home/NotBroke/frontend/node_modules/.bin/next start

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activer les services :

```bash
systemctl daemon-reload
systemctl enable notbroke-backend notbroke-frontend
systemctl start notbroke-backend notbroke-frontend

# Vérifier
systemctl status notbroke-backend
systemctl status notbroke-frontend
```

---

## 🚀 Déploiement sur Render

### Étape 1 : Créer une instance PostgreSQL

```
1. Se connecter à Render.com
2. Dashboard → New → PostgreSQL
3. Name: notbroke-db
4. PostgreSQL Version: 15 (ou 16)
5. Region: Closest to you
6. Create Database
```

Render vous fournira une connection string :

```
postgresql://user:password@host:port/database
```

### Étape 2 : Configurer le backend

```
1. New → Web Service
2. Repository: votre repo GitHub
3. Root Directory: backend
4. Build Command: pip install -r requirements.txt
5. Start Command: gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker
6. Environment Variables:
   - DATABASE_URL: (connection string PostgreSQL)
   - ENVIRONMENT: production
   - SECRET_KEY: (générer une clé sécurisée)
   - FRONTEND_URL: https://votre-frontend.onrender.com
7. Deploy
```

### Étape 3 : Configurer le frontend

```
1. New → Web Service
2. Repository: votre repo GitHub
3. Root Directory: frontend
4. Build Command: npm ci && npm run build
5. Start Command: npm start
6. Environment Variables:
   - NEXT_PUBLIC_API_BASE_URL: https://votre-backend.onrender.com
7. Deploy
```

### Étape 4 : Vérifier le déploiement

```
1. Attendre la fin du build (2-3 min)
2. Ouvrir l'URL du frontend
3. Tester la connexion/inscription
4. Vérifier les logs en cas d'erreur
```

---

## 🔧 Troubleshooting

### Erreur : "can't connect to PostgreSQL"

**Causes possibles** :
- PostgreSQL n'est pas installé/lancé
- Connection string incorrecte
- Mauvais mot de passe

**Solution** :

```bash
# Vérifier la connection string
psql "postgresql://user:password@localhost:5432/notbroke_db"

# Vérifier PostgreSQL est lancé
sudo systemctl status postgresql

# Vérifier les credentials
sudo -u postgres psql
\du  # Lister les utilisateurs
```

### Erreur : "asyncpg not found"

```bash
pip install asyncpg==0.30.0
```

### Les données ne sont pas migrées

**Vérifier** :
1. SQLite (source) a des données : `SELECT count(*) FROM users;` (dans SQLite)
2. Script de migration a bien roulé
3. PostgreSQL (target) est accessible

```bash
# Relancer la migration
cd backend
python migrate_to_postgres.py
```

### Application lente après migration

**Solutions** :
1. Vérifier les indexes PostgreSQL :
   ```sql
   SELECT * FROM pg_stat_user_indexes;
   ```

2. Analyser une requête lente :
   ```sql
   EXPLAIN ANALYZE SELECT * FROM expenses WHERE user_id = 1;
   ```

3. Augmenter les ressources du serveur

---

## ✅ Checklist de migration

- [ ] PostgreSQL installé localement
- [ ] Base de données créée
- [ ] Utilisateur PostgreSQL créé
- [ ] `asyncpg` ajouté aux requirements.txt
- [ ] `.env` configuré avec PostgreSQL
- [ ] Migration des données réussie (si données existantes)
- [ ] Application testée localement
- [ ] Code poussé sur GitHub
- [ ] Instance PostgreSQL créée sur Render/VPS
- [ ] Backend déployé sur Render/VPS
- [ ] Frontend déployé sur Render/VPS
- [ ] Tests de l'application en production

---

## 📝 Notes importantes

**Sécurité** :
- Toujours utiliser des mots de passe forts pour PostgreSQL
- Jamais committer le .env avec les vrais secrets
- Utiliser des secrets différents pour dev et production

**Backups** :
- Sur Render : backups automatiques (inclus)
- Sur VPS : configurer des backups manuels avec `pg_dump`

**Performance** :
- PostgreSQL a besoin de plus de ressources que SQLite
- Vérifier les logs de performance
- Utiliser EXPLAIN ANALYZE pour optimiser les requêtes lentes

---

## Support

Pour toute question ou erreur :
1. Vérifier les logs : `journalctl -u notbroke-backend`
2. Consulter la documentation PostgreSQL officielle
3. Vérifier que la connection string est correcte

