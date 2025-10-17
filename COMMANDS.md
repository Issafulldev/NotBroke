# 🚀 Commandes Rapides - NotBroke

## Développement Local

### Démarrage Complet
```bash
./start-local.sh
```

### Démarrage Manuel
```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

### Tests
```bash
# Tester la connexion API (remplacez USERNAME et PASSWORD par vos propres identifiants)
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "VOTRE_USERNAME", "password": "VOTRE_PASSWORD"}'
```

## URLs Importantes

- **Frontend Local**: http://localhost:3000
- **Backend Local**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

## Configuration Utilisateur

- **Première connexion**: Utilisez l'interface d'inscription pour créer votre compte administrateur
- **Migration**: Utilisez `python3 migration_script.py` pour initialiser un utilisateur si nécessaire

## Déploiement Production

### Préparation
```bash
# Générer une clé secrète
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Push vers GitHub (déclenche le déploiement)
git push origin main
```

### Variables d'Environnement

#### Backend
```
ENVIRONMENT=production
SECRET_KEY=votre-cle-secrete
DATABASE_URL=sqlite+aiosqlite:///./expense.db
FRONTEND_URL=https://your-frontend-domain.com
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Frontend
```
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.com
```

## Dépannage

### Port Occupé
```bash
lsof -ti:8000 && kill -9 $(lsof -ti:8000)
```

### Réinstaller Dépendances
```bash
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
```

### Recréer Utilisateur Admin
```bash
python3 migration_script.py
```

## Maintenance

### Mettre à Jour
```bash
# Backend
cd backend && source venv/bin/activate && pip install -r requirements.txt

# Frontend
cd frontend && npm update

# Push des changements
git add . && git commit -m "update" && git push
```
