"""sync category id sequence

Revision ID: 032ca5d6ab81
Revises: 24ae781c7b3f
Create Date: 2025-10-30 17:50:57.534106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '032ca5d6ab81'
down_revision = '24ae781c7b3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(
            sa.text(
                "SELECT setval(pg_get_serial_sequence('categories', 'id'), "
                "COALESCE((SELECT MAX(id) FROM categories), 0) + 1, false)"
            )
        )


def downgrade() -> None:
    pass
