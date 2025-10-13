# 🚂 Déploiement sur Railway - Guide Rapide

## Prérequis
- Compte Railway créé
- Repository GitHub connecté à Railway
- Variables d'environnement configurées

## Déploiement Backend + Frontend

### 1. Configuration Initiale

```bash
# Cloner le repo (si pas déjà fait)
git clone https://github.com/votre-username/notbroke.git
cd notbroke

# Générer une clé secrète pour le backend
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
# Copiez cette clé pour l'étape suivante
```

### 2. Déploiement Backend

1. **Connecter le backend à Railway :**
   ```bash
   cd backend
   railway link
   ```

2. **Configurer les variables d'environnement dans le dashboard Railway :**
   ```
   ENVIRONMENT=production
   SECRET_KEY=votre-cle-secrete-generee
   DATABASE_URL=sqlite+aiosqlite:///./expense.db
   FRONTEND_URL=https://your-frontend-service.railway.app
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. **Déployer le backend :**
   ```bash
   railway up
   ```

### 3. Déploiement Frontend

1. **Ajouter le service frontend :**
   ```bash
   railway add --name frontend
   ```

2. **Connecter le frontend à Railway :**
   ```bash
   cd ../frontend
   railway link
   ```

3. **Configurer les variables d'environnement dans le dashboard Railway :**
   ```
   NEXT_PUBLIC_API_BASE_URL=https://your-backend-service-name.railway.app
   NODE_ENV=production
   ```

4. **Déployer le frontend :**
   ```bash
   railway up
   ```

## Vérification du Déploiement

### Commandes utiles :
```bash
# Voir le statut de tous les services
railway status

# Voir les logs du backend
railway logs --service backend

# Voir les logs du frontend
railway logs --service frontend

# Ouvrir les services dans le navigateur
railway open
```

### URLs attendues :
- **Frontend** : `https://your-frontend-service.railway.app`
- **Backend API** : `https://your-backend-service.railway.app`
- **Documentation API** : `https://your-backend-service.railway.app/docs`

## Résolution des Problèmes

### Problème : "Service not found"
```bash
# Reconnecter les services
railway link
```

### Problème : Variables d'environnement manquantes
- Vérifiez le dashboard Railway
- Redéployez après modification : `railway up`

### Problème : Frontend ne se connecte pas au backend
- Vérifiez que `NEXT_PUBLIC_API_BASE_URL` pointe vers le bon service backend
- Vérifiez les logs pour les erreurs CORS

## Maintenance

### Mises à jour :
```bash
# Push vos changements
git add .
git commit -m "Update description"
git push origin main

# Railway déploie automatiquement
```

### Monitoring :
- Dashboard Railway pour l'usage CPU/RAM
- Logs disponibles via `railway logs`
- Métriques détaillées dans l'interface web Railway

## Support
- **Crédit gratuit** : $5/mois inclus
- **Limites** : 512 MB RAM par service, trafic raisonnable
- **Support** : Documentation Railway complète disponible

🎉 **Votre application est maintenant déployée et accessible gratuitement !**
