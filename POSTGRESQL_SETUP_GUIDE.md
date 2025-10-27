# 🚀 PostgreSQL Setup - Quick Start Guide

Bienvenue ! Voici un guide rapide pour mettre en place PostgreSQL pour NotBroke.

## 📦 Ce qui a été préparé pour vous

Votre application a été optimisée pour PostgreSQL avec :

✅ **requirements.txt** - Mis à jour avec `asyncpg` (driver PostgreSQL async)
✅ **migrate_to_postgres.py** - Script de migration automatisé (SQLite → PostgreSQL)
✅ **setup-postgres.sh** - Script d'automatisation de l'installation
✅ **MIGRATION_POSTGRESQL.md** - Guide détaillé (VPS, Render, Local)
✅ **README.md** - Documenté avec PostgreSQL

**Le code est 100% compatible** - Aucun changement required dans votre logique métier !

---

## 🎯 3 chemins possibles

### 1️⃣ **Chemin rapide (5 min)** - Si vous êtes sur macOS/Linux

```bash
cd backend
chmod +x setup-postgres.sh
./setup-postgres.sh
```

Le script va :
1. ✅ Installer PostgreSQL (si nécessaire)
2. ✅ Créer l'utilisateur `notbroke_user`
3. ✅ Créer la base `notbroke_db`
4. ✅ Générer le fichier `.env`

### 2️⃣ **Chemin manuel** - Si vous préférez contrôler chaque étape

```bash
# 1. Installer PostgreSQL manuellement
# macOS: brew install postgresql@15
# Linux: sudo apt install postgresql

# 2. Créer la base
psql postgres
CREATE USER notbroke_user WITH PASSWORD 'notbroke_password';
CREATE DATABASE notbroke_db OWNER notbroke_user;
\q

# 3. Créer .env
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://notbroke_user:notbroke_password@localhost:5432/notbroke_db
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
SECRET_KEY=dev_secret_key
EOF

# 4. Installer les dépendances
cd backend
pip install -r requirements.txt
```

### 3️⃣ **Chemin avec migration de données** - Si vous avez des données en SQLite

```bash
# 1. Faire les étapes 1-2 du chemin manuel
# 2. Installer les dépendances
cd backend
pip install -r requirements.txt

# 3. Lancer la migration
python migrate_to_postgres.py

# Le script va afficher un résumé détaillé
```

---

## ✅ Vérifier que tout fonctionne

```bash
# 1. Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 2. Terminal 2 - Frontend
cd frontend
npm run dev

# 3. Ouvrir http://localhost:3000 et tester
```

**Points de vérification** :
- [ ] Page de login s'affiche
- [ ] Inscription fonctionne
- [ ] Créer une catégorie fonctionne
- [ ] Ajouter une dépense fonctionne
- [ ] Voir les données fonctionne

---

## 📊 Fichiers créés/modifiés

```
backend/
├── requirements.txt          ✏️ Mis à jour (+ asyncpg)
├── migrate_to_postgres.py    ✨ Nouveau (migration automatisée)
├── setup-postgres.sh         ✨ Nouveau (automatisation setup)
├── .env                      ⚙️ À créer (via setup ou manual)
└── app/
    └── database.py           ✅ Déjà compatible PostgreSQL

root/
├── README.md                 ✏️ Mis à jour (PostgreSQL docs)
├── MIGRATION_POSTGRESQL.md   ✨ Nouveau (guide détaillé)
└── POSTGRESQL_SETUP_GUIDE.md ✨ Ce fichier!
```

---

## 🔄 Prochaines étapes

### Développement local
1. ✅ Configurer PostgreSQL (choix 1, 2 ou 3 ci-dessus)
2. ✅ Tester l'app localement
3. ✅ Committer les changements
4. ⏭️ **Ensuite** → Déployer sur Render/VPS

### Déploiement Render
Voir [MIGRATION_POSTGRESQL.md](./MIGRATION_POSTGRESQL.md#déploiement-sur-render)

```bash
# 1. Sur Render.com :
#    - Créer une instance PostgreSQL
#    - Copier la connection string

# 2. Déployer le backend
#    - Root: backend
#    - Command: gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker
#    - Env: DATABASE_URL=<connection_string>

# 3. Déployer le frontend
#    - Root: frontend
#    - Command: npm start
```

### Déploiement VPS Hostinger
Voir [MIGRATION_POSTGRESQL.md](./MIGRATION_POSTGRESQL.md#déploiement-sur-vps-hostinger)

---

## 🆘 En cas de problème

### "Command not found: postgres" ou "psql: command not found"

PostgreSQL n'est pas dans le PATH. Essayez :

```bash
# macOS
which psql
# ou
/usr/local/var/postgres

# Linux
sudo -u postgres psql
```

### "connection refused" ou "Erreur de connexion"

```bash
# Vérifier que PostgreSQL est lancé
# macOS
brew services list

# Linux
sudo systemctl status postgresql
```

### "Erreur d'authentification"

Vérifier la connection string dans `.env` :

```bash
DATABASE_URL=postgresql+asyncpg://notbroke_user:notbroke_password@localhost:5432/notbroke_db
```

Les credentials doivent correspondre à ceux que vous avez créés.

### "asyncpg not found"

```bash
pip install asyncpg==0.30.0
```

### "Table already exists"

Si vous relancez la migration, le script créera les tables. Pour recommencer :

```bash
# Réinitialiser la base PostgreSQL
psql -U postgres
DROP DATABASE notbroke_db;
CREATE DATABASE notbroke_db OWNER notbroke_user;
\q

# Relancer la migration
python migrate_to_postgres.py
```

---

## 💡 Conseils

### Mot de passe de développement
Le script de setup utilise `notbroke_password` pour la dev.

**Pour la production**, générez une clé sécurisée :

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Performance - Vérifier les logs

```bash
# Lancer avec verbose pour voir les requêtes SQL
SQLALCHEMY_ECHO=1 uvicorn app.main:app
```

### Backup PostgreSQL

```bash
# Exporter la base
pg_dump -U notbroke_user notbroke_db > backup.sql

# Restaurer
psql -U notbroke_user notbroke_db < backup.sql
```

---

## 📚 Documentation complète

- **Setup local** → [MIGRATION_POSTGRESQL.md - Local](./MIGRATION_POSTGRESQL.md#migration-en-développement-local)
- **VPS Hostinger** → [MIGRATION_POSTGRESQL.md - VPS](./MIGRATION_POSTGRESQL.md#déploiement-sur-vps-hostinger)
- **Render** → [MIGRATION_POSTGRESQL.md - Render](./MIGRATION_POSTGRESQL.md#déploiement-sur-render)
- **Troubleshooting** → [MIGRATION_POSTGRESQL.md - Troubleshooting](./MIGRATION_POSTGRESQL.md#troubleshooting)

---

## 🎯 Résumé

Vous avez maintenant un setup production-ready avec :

✅ Code compatible SQLite et PostgreSQL
✅ Scripts de migration automatisés
✅ Documentation complète
✅ Prêt pour Render, VPS, ou n'importe quel hébergeur

**Félicitations !** 🎉 Vous êtes à 5 minutes d'avoir une app production-ready.

---

*Questions ?* Consultez la section [Troubleshooting](./MIGRATION_POSTGRESQL.md#troubleshooting) du guide complet.
