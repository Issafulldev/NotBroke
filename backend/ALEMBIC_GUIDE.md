# Alembic Migrations Guide

This project uses Alembic for database migrations to manage schema changes in a version-controlled way.

## Setup

Alembic is already configured in this project. The configuration files are:
- `alembic.ini` - Main configuration file
- `alembic/env.py` - Migration environment setup
- `alembic/versions/` - Directory containing migration scripts

## Creating Migrations

### Initial Migration (if tables already exist)

If you already have tables created via `init_db()`, create an initial migration:

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Initial migration"
```

This will create a migration file in `alembic/versions/` that captures the current state of your database.

### Creating New Migrations

After modifying models in `app/models.py`:

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Description of changes"
```

Review the generated migration file before applying it.

### Manual Migrations

For complex changes that Alembic can't auto-detect:

```bash
alembic revision -m "Description of changes"
```

Then manually edit the migration file in `alembic/versions/`.

## Applying Migrations

### Apply all pending migrations:

```bash
alembic upgrade head
```

### Apply to a specific revision:

```bash
alembic upgrade <revision_id>
```

### Rollback to previous version:

```bash
alembic downgrade -1
```

### Rollback to a specific revision:

```bash
alembic downgrade <revision_id>
```

## Checking Migration Status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Production Deployment

Before deploying to production:

1. **Review migrations**: Always review migration files before applying in production
2. **Backup database**: Create a backup before running migrations
3. **Test migrations**: Test migrations on a staging environment first
4. **Apply migrations**: Run `alembic upgrade head` during deployment

## Best Practices

1. **One migration per feature**: Create separate migrations for different features
2. **Review auto-generated code**: Always review and test auto-generated migrations
3. **Test downgrades**: Ensure migrations can be rolled back safely
4. **Don't edit old migrations**: Never modify existing migrations, create new ones
5. **Commit migrations**: Always commit migration files to version control

## Troubleshooting

### Migration conflicts

If you have conflicts with existing migrations:

```bash
# Check current database state
alembic current

# Check what migrations exist
alembic history

# Stamp database to current state (if needed)
alembic stamp head
```

### SQLite vs PostgreSQL

The migration system handles both SQLite and PostgreSQL automatically. The `env.py` file converts async URLs to sync URLs for Alembic compatibility.

## Example Workflow

```bash
# 1. Make changes to models.py
# Edit app/models.py

# 2. Generate migration
alembic revision --autogenerate -m "Add new field to Expense model"

# 3. Review generated migration
# Check alembic/versions/XXXX_add_new_field_to_expense_model.py

# 4. Apply migration
alembic upgrade head

# 5. Test the changes
# Run your application and verify everything works

# 6. Commit to git
git add alembic/versions/XXXX_*.py
git commit -m "Add migration for new Expense field"
```

