"""drop global unique constraint on category name

Revision ID: 24ae781c7b3f
Revises: 429e7e5bb4f7
Create Date: 2025-10-30 16:51:56.703871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24ae781c7b3f'
down_revision = '429e7e5bb4f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)

    unique_constraints = inspector.get_unique_constraints('categories')
    has_global_unique = any(set(uc['column_names']) == {'name'} for uc in unique_constraints)

    if has_global_unique:
        if dialect == 'sqlite':
            op.execute(sa.text('PRAGMA foreign_keys=OFF'))
            op.execute(sa.text(
                """
                CREATE TABLE categories_tmp (
                    id INTEGER NOT NULL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    user_id INTEGER,
                    FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE SET NULL,
                    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
                )
                """
            ))
            op.execute(sa.text(
                """
                INSERT INTO categories_tmp (id, name, description, parent_id, user_id)
                SELECT id, name, description, parent_id, user_id FROM categories
                """
            ))
            op.execute(sa.text('DROP TABLE categories'))
            op.execute(sa.text('ALTER TABLE categories_tmp RENAME TO categories'))
            op.execute(sa.text('PRAGMA foreign_keys=ON'))
            # Recreate primary key helper index if missing (no-op if already present)
            op.execute(sa.text('CREATE INDEX IF NOT EXISTS ix_categories_id ON categories (id)'))
        else:
            for constraint in unique_constraints:
                if set(constraint['column_names']) == {'name'} and constraint['name']:
                    with op.batch_alter_table('categories') as batch_op:
                        batch_op.drop_constraint(constraint['name'], type_='unique')
                    break

    # Replace old helper index if it still exists
    op.execute(sa.text('DROP INDEX IF EXISTS idx_categories_user_name'))
    op.create_index(
        'idx_categories_user_parent_name',
        'categories',
        ['user_id', 'parent_id', 'name'],
        unique=False,
    )


def downgrade() -> None:
    # Drop the new composite index
    op.drop_index('idx_categories_user_parent_name', table_name='categories')

    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)

    unique_constraints = inspector.get_unique_constraints('categories')
    has_global_unique = any(set(uc['column_names']) == {'name'} for uc in unique_constraints)

    if not has_global_unique:
        if dialect == 'sqlite':
            op.execute(sa.text('PRAGMA foreign_keys=OFF'))
            op.execute(sa.text(
                """
                CREATE TABLE categories_tmp (
                    id INTEGER NOT NULL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    parent_id INTEGER,
                    user_id INTEGER,
                    UNIQUE (name),
                    FOREIGN KEY(parent_id) REFERENCES categories (id) ON DELETE SET NULL,
                    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
                )
                """
            ))
            op.execute(sa.text(
                """
                INSERT INTO categories_tmp (id, name, description, parent_id, user_id)
                SELECT id, name, description, parent_id, user_id FROM categories
                """
            ))
            op.execute(sa.text('DROP TABLE categories'))
            op.execute(sa.text('ALTER TABLE categories_tmp RENAME TO categories'))
            op.execute(sa.text('PRAGMA foreign_keys=ON'))
            op.execute(sa.text('CREATE INDEX IF NOT EXISTS ix_categories_id ON categories (id)'))
        else:
            with op.batch_alter_table('categories') as batch_op:
                batch_op.create_unique_constraint('categories_name_key', ['name'])

    # Restore the previous helper index
    op.execute(sa.text('CREATE INDEX IF NOT EXISTS idx_categories_user_name ON categories (user_id, name)'))
