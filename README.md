# Plateforme de gestion des dépenses

Cette application full-stack permet de gérer des catégories de dépenses, d'ajouter des dépenses par catégorie et d'obtenir un résumé mensuel. Elle est composée d'un backend FastAPI (Python) et d'un frontend React.

## Aperçu de l'architecture

- `backend/` : API FastAPI asynchrone, utilisant SQLAlchemy + SQLite.
- `frontend/` : application React créée avec Vite, utilisant React Query, Axios, React Hook Form et Zustand.

## Prérequis

- Python 3.11+ (recommandé : utiliser la version fournie par `uv` ou `pyenv`).
- Node.js 18+.
- npm 9+ (installé avec Node).

## Backend

### Installation

```bash
cd /Users/Issa/expense-platform/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # À créer si nécessaire
```

> La configuration FastAPI actuelle utilise SQLite via `DATABASE_URL`. Vous pouvez le surcharger par variable d'environnement si besoin.

### Lancement du serveur

```bash
cd /Users/Issa/expense-platform/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

L'API répond par défaut sur `http://127.0.0.1:8000`.

### Endpoints principaux

- `POST /categories` : crée une catégorie.
- `GET /categories` : liste les catégories.
- `POST /expenses` : ajoute une dépense.
- `GET /categories/{category_id}/expenses` : liste les dépenses d'une catégorie.
- `GET /summary` : retourne le résumé mensuel.

## Frontend

### Installation

```bash
cd /Users/Issa/expense-platform/frontend
npm install
```

### Configuration

Créez un fichier `.env` à la racine du dossier `frontend/` si vous souhaitez personnaliser l'URL de l'API :

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Lancer l'application

```bash
cd /Users/Issa/expense-platform/frontend
npm run dev
```

Ensuite ouvrez `http://localhost:5173` dans votre navigateur.

## Flux d'utilisation

1. Créez une catégorie via le formulaire à gauche.
2. Sélectionnez une catégorie pour l'activer.
3. Ajoutez des dépenses via le formulaire central.
4. Consultez la liste des dépenses et le résumé mensuel (total global + par catégorie).

## Tests / lint

- Backend : à définir en fonction de votre environnement (pytest recommandé).
- Frontend : `npm run lint` (ESLint).

## Prochaines étapes possibles

- Authentification et gestion multi-utilisateur.
- Export des données (CSV/Excel).
- Visualisations graphiques (charts) pour les résumés.

