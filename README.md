# NotBroke - Expense Management Platform

A modern full-stack application for managing your expense categories, adding transactions, and getting detailed summaries. It includes a robust FastAPI backend and an interactive Next.js frontend.

## 🚀 Quick Start - Development & Production

### **Option 1: Développement Local (Recommandé pour commencer)**

```bash
# Démarrage rapide (tout en un)
./start-local.sh

# Ou manuellement :
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && bun run dev
```

**URLs de développement:**
- Frontend: `http://localhost:3000`
- Backend API: `http://127.0.0.1:8000`
- Documentation: `http://127.0.0.1:8000/docs`

### **Option 2: Déploiement Production**

1. **Fork/Clone this repository** to your GitHub account
2. **Link to Railway** for backend deployment (automatic on push)
3. **Link to Netlify** for frontend deployment (automatic on push)
4. **Set environment variables** on both platforms (see sections below)
5. **Push to main branch** - everything deploys automatically!

**URLs de production:**
- Frontend: `https://your-site.netlify.app`
- Backend: `https://your-backend.railway.app`

## Main Features

- **Category Management**: Create, edit, delete and organize categories hierarchically (sub-categories supported).
- **Expense Management**: Add, edit, delete and perform advanced searches by category, date and amount.
- **Monthly Summaries**: Automatic calculation of totals by period and category.
- **Data Export**: Export to CSV or XLSX for external analysis.
- **Intuitive User Interface**: Modern design with Tailwind CSS, modals and reusable components.

## Architecture Overview

- **Backend**: Asynchronous FastAPI API with SQLAlchemy + SQLite, optimized for Railway's free tier with connection pooling, pagination, JWT authentication, and production-ready configurations.
- **Frontend**: Next.js application (React 19) with React Query for data management, Zustand for global state, and Tailwind CSS for styling.
- **Database**: SQLite with performance indexes and optimized for low-memory environments.
- **Deployment**: Railway-optimized with custom startup scripts and environment-specific configurations.

## Prerequisites

- Python 3.11+ (recommended: use `uv` or `pyenv` for version management).
- Node.js 18+ (LTS recommended).
- Bun, npm or yarn (Bun recommended for better performance).

## Backend

### Installation and Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> The backend uses SQLite by default via the `DATABASE_URL` variable. You can override it in a `.env` file if needed (e.g.: `DATABASE_URL=sqlite:///./expense.db`).

### Starting the Server

For development:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

For production (Railway deployment):
```bash
# The application will be automatically started by start.sh
# which includes performance optimizations for the free tier
```

The API will be accessible at `http://127.0.0.1:8000` (development) or your Railway domain (production).

**Note**: The backend includes performance optimizations specifically designed for Railway's free tier, including connection pooling, pagination, and memory-efficient configurations.

### Main Endpoints

- **Authentication**:
  - `POST /auth/register`: Register a new user.
  - `POST /auth/login`: Login and get JWT token.

- **Categories**:
  - `POST /categories`: Create a new category.
  - `GET /categories`: List all user categories.
  - `GET /categories/{id}`: Get a specific category.
  - `PATCH /categories/{id}`: Update a category.
  - `DELETE /categories/{id}`: Delete a category.

- **Expenses**:
  - `POST /expenses`: Add a new expense.
  - `GET /expenses`: Search expenses (with filters by category, date, pagination).
  - `GET /categories/{category_id}/expenses`: List expenses for a category (paginated).
  - `PATCH /expenses/{id}`: Update an expense.
  - `DELETE /expenses/{id}`: Delete an expense.

- **Summaries and Export**:
  - `GET /summary`: Get monthly summary (totals by category and period).
  - `GET /expenses/export`: Export expenses to CSV or XLSX.

## Frontend

### Installation and Setup

```bash
cd frontend
bun install
```

### Configuration

Create a `.env.local` file at the root of the `frontend/` folder to customize the API URL:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> If not defined, the default API is used.

### Starting the Application

```bash
cd frontend
bun run dev
```

Open `http://localhost:3000` in your browser (Next.js default port).

### Frontend Features

- **Category Management**: Modal forms for creating/editing categories with hierarchical support.
- **Expense Management**: Interface for adding expenses with category selection.
- **Search and Filters**: Search panel with filters by date and category.
- **Monthly Summary**: Display of totals and simple charts.
- **Export**: Download data in CSV or XLSX format.
- **UI/UX**: Reusable components (shadcn/ui-like) with animations and responsive design.

## Typical Usage Flow

1. **Set up categories**: Use the categories panel to create a hierarchy (e.g.: "Transportation / Car" as a subcategory).
2. **Add expenses**: Select a category and enter the amount and details via the main form.
3. **Browse and filter**: Use the search panel to filter by date or category.
4. **Analyze data**: Check the monthly summary to see totals by category and export if needed.
5. **Manage data**: Edit or delete categories/expenses via modals.

## Development and Testing

- **Linting**:
  - Backend: Use `flake8` or `black` if configured (no specific script in the current project).
  - Frontend: `bun run lint` (ESLint configured).

- **Testing**:
  - Backend: No tests currently defined; recommend `pytest` for unit tests.
  - Frontend: No tests defined; integrate `Jest` or `Vitest` for React tests.

- **Database**: The `expense.db` and `expense_backup.db` files are used for persistence.

## 💻 Développement Local

### **Configuration Requise**

- **Python 3.11+** avec environnement virtuel
- **Node.js 18+** and Bun (recommended)
- **Git** pour le contrôle de version

### **Installation et Configuration**

#### **Backend Setup**
```bash
cd backend

# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Frontend Setup**
```bash
cd frontend

# Installer les dépendances
bun install

# Lancer le serveur de développement
bun run dev
```

### **Variables d'Environnement Locales**

#### **Backend (.env)**
```bash
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./expense.db
FRONTEND_URL=http://localhost:3000
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### **Frontend (.env.local)**
```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### **Démarrage Rapide**
```bash
# Utiliser le script automatique
./start-local.sh

# Ou démarrer manuellement
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && bun run dev
```

### **Identifiants de Développement**
- **Username**: `admin`
- **Password**: `admin123`

### **Tests Locaux**
1. **Backend**: `http://127.0.0.1:8000/docs`
2. **Frontend**: `http://localhost:3000`
3. **Connexion**: Utilisez les identifiants ci-dessus

### **Dépannage Développement Local**

#### **Problème: "Address already in use"**
```bash
# Trouver le processus
lsof -ti:8000
# Tuer le processus
kill -9 PID_NUMBER
```

#### **Problème: "Module not found"**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

#### **Problème: Frontend ne se connecte pas**
- Vérifiez que le backend tourne sur le port 8000
- Vérifiez le fichier `.env.local` du frontend
- Redémarrez les deux serveurs

#### **Problème: Utilisateur admin non trouvé**
```bash
cd /Users/Issa/NotBroke
python3 migration_script.py
```

## 🔧 Environment Variables Setup

### Railway (Backend) Variables
Set these in your Railway project dashboard:

```bash
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key-here
DATABASE_URL=sqlite+aiosqlite:///./expense.db
FRONTEND_URL=https://your-netlify-site.netlify.app
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Netlify (Frontend) Variables
Set these in your Netlify site dashboard:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-railway-backend.railway.app
```

## 🚂 Railway Deployment (Free Tier Optimized)

This backend is optimized for deployment on [Railway](https://railway.app) using their free tier (512 MB RAM, 1 GB storage).

### Railway Configuration Files

The project includes optimized configuration for Railway deployment:

- **`runtime.txt`**: Specifies Python 3.11
- **`Procfile`**: Defines the web process using the optimized startup script
- **`start.sh`**: Custom startup script with performance optimizations
- **`.env.example`**: Template for required environment variables

### Environment Variables for Railway

Set these variables in your Railway project settings:

```bash
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key-here
DATABASE_URL=sqlite+aiosqlite:///./expense.db
FRONTEND_URL=https://your-frontend-domain.com
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Deployment Steps

1. **Generate a secure SECRET_KEY**:
   ```bash
   python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
   ```

2. **Set environment variables** in Railway dashboard

3. **Deploy**:
   ```bash
   railway up
   ```

### Performance Optimizations Applied

- **Database**: Optimized connection pooling (pool_size=5, max_overflow=10)
- **Memory**: Pagination implemented for large datasets (50 items per page)
- **Security**: Production-ready CORS configuration and secure JWT handling
- **Timeouts**: 30-second request timeout to prevent hanging connections
- **Indexes**: Database indexes on frequently queried fields
- **Workers**: Single worker configuration for free tier memory limits

### Production Features

- **CORS**: Restricted to specific frontend domains in production
- **Documentation**: API docs hidden in production for security
- **Logging**: Reduced logging level for better performance
- **Error Handling**: Proper error responses and timeouts

## Recent Updates and Improvements

✅ **Authentication System**: JWT-based login/logout fully implemented with secure token handling
✅ **Railway Optimization**: Complete optimization for free tier deployment (512 MB RAM, 1 GB storage)
✅ **Performance Enhancements**: Database indexes, pagination, connection pooling, and memory optimizations
✅ **Production Security**: Environment-based configuration, CORS restrictions, and secure defaults

## Future Enhancements

- **Visualizations**: Integration of Chart.js or similar for advanced data visualization
- **Notifications**: Budget alerts and expense notifications system
- **Advanced Caching**: Redis integration for high-traffic scenarios
- **Monitoring Dashboard**: Integration with Railway's monitoring tools
- **API Rate Limiting**: Request throttling for enhanced security
- **Multi-language Support**: Internationalization for broader user base

## 🎯 Post-Deployment Checklist

After successful deployment:

1. **Test Authentication**: Register/login on your frontend
2. **Test CRUD Operations**: Create categories and expenses
3. **Test API Communication**: Verify frontend-backend communication
4. **Check CORS**: Ensure no CORS errors
5. **Monitor Performance**: Check Railway and Netlify dashboards
6. **Update DNS** (optional): Point custom domain if needed

## 📊 Production Monitoring

- **Railway Dashboard**: Monitor CPU, RAM, and database usage
- **Netlify Dashboard**: Check build logs and analytics
- **Error Tracking**: Set up error monitoring (e.g., Sentry) for production

## Author and License

Developed by [Issafulldev](https://github.com/Issafulldev). This project is open-source under the MIT license.

