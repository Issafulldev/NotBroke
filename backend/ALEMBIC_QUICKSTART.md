# Database Migrations with Alembic

## Quick Start

```bash
# Create initial migration (if needed)
alembic revision --autogenerate -m "Initial migration"

# Apply all migrations
alembic upgrade head

# Check current revision
alembic current
```

## Commands

- `alembic revision --autogenerate -m "message"` - Create new migration
- `alembic upgrade head` - Apply all pending migrations
- `alembic downgrade -1` - Rollback one migration
- `alembic current` - Show current revision
- `alembic history` - Show all migrations

See `ALEMBIC_GUIDE.md` for detailed documentation.

