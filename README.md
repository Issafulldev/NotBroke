# NotBroke - Expense Management Platform

A modern full-stack application for managing your expense categories, adding transactions, and getting detailed summaries. It includes a robust FastAPI backend and an interactive Next.js frontend.

## Main Features

- **Category Management**: Create, edit, delete and organize categories hierarchically (sub-categories supported).
- **Expense Management**: Add, edit, delete and perform advanced searches by category, date and amount.
- **Monthly Summaries**: Automatic calculation of totals by period and category.
- **Data Export**: Export to CSV or XLSX for external analysis.
- **Intuitive User Interface**: Modern design with Tailwind CSS, modals and reusable components.

## Architecture Overview

- **Backend**: Asynchronous FastAPI API with SQLAlchemy + SQLite, supporting complete CRUD operations, search and export.
- **Frontend**: Next.js application (React 19) with React Query for data management, Zustand for global state, and Tailwind CSS for styling.

## Prerequisites

- Python 3.11+ (recommended: use `uv` or `pyenv` for version management).
- Node.js 18+ (LTS recommended).
- npm or yarn (installed with Node.js).

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

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`.

### Main Endpoints

- **Categories**:
  - `POST /categories`: Create a new category.
  - `GET /categories`: List all categories.
  - `GET /categories/{id}`: Get a specific category.
  - `PATCH /categories/{id}`: Update a category.
  - `DELETE /categories/{id}`: Delete a category.

- **Expenses**:
  - `POST /expenses`: Add a new expense.
  - `GET /expenses`: Search expenses (with filters by category, date).
  - `GET /categories/{category_id}/expenses`: List expenses for a category.
  - `PATCH /expenses/{id}`: Update an expense.
  - `DELETE /expenses/{id}`: Delete an expense.

- **Summaries and Export**:
  - `GET /summary`: Get monthly summary (totals by category and period).
  - `GET /expenses/export`: Export expenses to CSV or XLSX.

## Frontend

### Installation and Setup

```bash
cd frontend
npm install
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
npm run dev
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
  - Frontend: `npm run lint` (ESLint configured).

- **Testing**:
  - Backend: No tests currently defined; recommend `pytest` for unit tests.
  - Frontend: No tests defined; integrate `Jest` or `Vitest` for React tests.

- **Database**: The `expense.db` and `expense_backup.db` files are used for persistence.

## Next Steps and Improvements

- **Authentication**: Add login/logout system with JWT.
- **Visualizations**: Integration of libraries like Chart.js for advanced charts.
- **Notifications**: Alerts for budget overruns.
- **Optimizations**: Migration to PostgreSQL for production, add caching (Redis).
- **Deployment**: Docker scripts to facilitate deployment.

## Author and License

Developed by [Issafulldev](https://github.com/Issafulldev). This project is open-source under the MIT license.

