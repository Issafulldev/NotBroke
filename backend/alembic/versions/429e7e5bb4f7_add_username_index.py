"""add_username_index

Revision ID: 429e7e5bb4f7
Revises: f04fa9f5c2f7
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '429e7e5bb4f7'
down_revision = 'f04fa9f5c2f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajouter un index sur username pour améliorer les performances des requêtes de login
    # Cet index est déjà créé par l'unique constraint, mais on le rend explicite pour PostgreSQL
    # Note: Sur PostgreSQL, l'unique constraint crée automatiquement un index, mais on s'assure qu'il existe
    # Pour SQLite, cela créera un index explicite
    op.create_index(
        'idx_users_username',
        'users',
        ['username'],
        unique=True,
        if_not_exists=True
    )


def downgrade() -> None:
    # Supprimer l'index (mais garder la contrainte unique)
    op.drop_index('idx_users_username', table_name='users')

