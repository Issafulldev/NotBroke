# NotBroke - Plateforme de gestion des dépenses

Une application full-stack moderne pour gérer vos catégories de dépenses, ajouter des transactions et obtenir des résumés détaillés. Elle comprend un backend API robuste avec FastAPI et un frontend interactif avec Next.js.

## Fonctionnalités principales

- **Gestion des catégories** : Création, modification, suppression et organisation hiérarchique des catégories (sous-catégories supportées).
- **Gestion des dépenses** : Ajout, modification, suppression et recherche avancée par catégorie, date et montant.
- **Résumés mensuels** : Calcul automatique des totaux par période et par catégorie.
- **Export des données** : Export en CSV ou XLSX pour analyse externe.
- **Interface utilisateur intuitive** : Design moderne avec Tailwind CSS, modales et composants réutilisables.

## Aperçu de l'architecture

- **Backend** : API FastAPI asynchrone avec SQLAlchemy + SQLite, supportant les opérations CRUD complètes, recherche et export.
- **Frontend** : Application Next.js (React 19) avec React Query pour la gestion des données, Zustand pour l'état global, et Tailwind CSS pour le styling.

## Prérequis

- Python 3.11+ (recommandé : utiliser `uv` ou `pyenv` pour la gestion des versions).
- Node.js 18+ (LTS recommandé).
- npm ou yarn (installé avec Node.js).

## Backend

### Installation et configuration

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
```

> Le backend utilise SQLite par défaut via la variable `DATABASE_URL`. Vous pouvez la surcharger dans un fichier `.env` si nécessaire (ex. : `DATABASE_URL=sqlite:///./expense.db`).

### Lancement du serveur

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

L'API sera accessible sur `http://127.0.0.1:8000`.

### Endpoints principaux

- **Catégories** :
  - `POST /categories` : Créer une nouvelle catégorie.
  - `GET /categories` : Lister toutes les catégories.
  - `GET /categories/{id}` : Obtenir une catégorie spécifique.
  - `PATCH /categories/{id}` : Mettre à jour une catégorie.
  - `DELETE /categories/{id}` : Supprimer une catégorie.

- **Dépenses** :
  - `POST /expenses` : Ajouter une nouvelle dépense.
  - `GET /expenses` : Rechercher des dépenses (avec filtres par catégorie, date).
  - `GET /categories/{category_id}/expenses` : Lister les dépenses d'une catégorie.
  - `PATCH /expenses/{id}` : Mettre à jour une dépense.
  - `DELETE /expenses/{id}` : Supprimer une dépense.

- **Résumés et export** :
  - `GET /summary` : Obtenir le résumé mensuel (totaux par catégorie et période).
  - `GET /expenses/export` : Exporter les dépenses en CSV ou XLSX.

## Frontend

### Installation et configuration

```bash
cd frontend
npm install
```

### Configuration

Créez un fichier `.env.local` à la racine du dossier `frontend/` pour personnaliser l'URL de l'API :

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> Si non défini, l'API par défaut est utilisée.

### Lancer l'application

```bash
cd frontend
npm run dev
```

Ouvrez `http://localhost:3000` dans votre navigateur (port par défaut de Next.js).

### Fonctionnalités du frontend

- **Gestion des catégories** : Formulaires modaux pour créer/éditer des catégories avec support hiérarchique.
- **Gestion des dépenses** : Interface pour ajouter des dépenses avec sélection de catégorie.
- **Recherche et filtres** : Panel de recherche avec filtres par date et catégorie.
- **Résumé mensuel** : Affichage des totaux et graphiques simples.
- **Export** : Téléchargement des données en CSV ou XLSX.
- **UI/UX** : Composants réutilisables (shadcn/ui-like) avec animations et responsive design.

## Flux d'utilisation typique

1. **Configurer les catégories** : Utilisez le panneau de catégories pour créer une hiérarchie (ex. : "Transport / Voiture" comme sous-catégorie).
2. **Ajouter des dépenses** : Sélectionnez une catégorie et saisissez le montant et les détails via le formulaire principal.
3. **Consulter et filtrer** : Utilisez le panneau de recherche pour filtrer par date ou catégorie.
4. **Analyser les données** : Consultez le résumé mensuel pour voir les totaux par catégorie et exporter si besoin.
5. **Gérer les données** : Modifiez ou supprimez des catégories/dépenses via les modales.

## Développement et tests

- **Linting** :
  - Backend : Utilisez `flake8` ou `black` si configuré (pas de script spécifique dans le projet actuel).
  - Frontend : `npm run lint` (ESLint configuré).

- **Tests** :
  - Backend : Aucun test défini actuellement ; recommandez `pytest` pour les tests unitaires.
  - Frontend : Aucun test défini ; intégrez `Jest` ou `Vitest` pour les tests React.

- **Base de données** : Les fichiers `expense.db` et `expense_backup.db` sont utilisés pour la persistance.

## Prochaines étapes et améliorations

- **Authentification** : Ajout d'un système de login/logout avec JWT.
- **Visualisations** : Intégration de bibliothèques comme Chart.js pour des graphiques avancés.
- **Notifications** : Alertes pour les dépassements de budget.
- **Optimisations** : Migration vers PostgreSQL pour la production, ajout de caching (Redis).
- **Déploiement** : Scripts Docker pour faciliter le déploiement.

## Auteur et licence

Développé par [Issafulldev](https://github.com/Issafulldev). Ce projet est open-source sous licence MIT.

