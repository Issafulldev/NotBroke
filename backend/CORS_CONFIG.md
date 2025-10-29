# Configuration CORS pour Render

## Problème CORS

Si vous voyez cette erreur :
```
Access to XMLHttpRequest at 'https://notbroke.onrender.com/categories?page=1&per_page=100' 
from origin 'https://notbrokefront.onrender.com' has been blocked by CORS policy
```

Cela signifie que votre backend ne permet pas les requêtes depuis votre frontend déployé.

## Solution

### Sur Render Dashboard

1. **Allez dans votre service backend** sur Render
2. **Onglet "Environment"**
3. **Ajoutez ou modifiez la variable d'environnement** :
   - **Clé** : `FRONTEND_URL`
   - **Valeur** : `https://notbrokefront.onrender.com`

   Si vous avez plusieurs frontends (dev + prod), vous pouvez séparer par des virgules :
   ```
   https://notbrokefront.onrender.com,http://localhost:3000
   ```

4. **Redéployez votre service backend** après avoir modifié les variables d'environnement

### Vérification

Après le redéploiement, vérifiez les logs du backend. Vous devriez voir :
```
🔒 Production CORS: Allowing origins https://notbrokefront.onrender.com
```

## Variables d'environnement nécessaires sur Render

### Backend Service
- `ENVIRONMENT` = `production`
- `DATABASE_URL` = votre URL PostgreSQL Render
- `SECRET_KEY` = une clé secrète générée (ex: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `FRONTEND_URL` = `https://notbrokefront.onrender.com`

### Frontend Service (si applicable)
- `NEXT_PUBLIC_API_BASE_URL` = `https://notbroke.onrender.com`

## Notes

- Le backend supporte maintenant **plusieurs origines** séparées par des virgules
- Assurez-vous que `FRONTEND_URL` commence par `http://` ou `https://`
- En production, CORS est strictement configuré pour la sécurité (credentials autorisés)

