"""Add currency table

Revision ID: d8975cbcf4de
Revises: e3a27b8b851d
Create Date: 2025-03-23 08:31:10.019986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8975cbcf4de'
down_revision: Union[str, None] = 'e3a27b8b851d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создаёт таблицу валют"""
    op.create_table(
        'currency',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('symbol', sa.String(length=10), nullable=False)
    )


def downgrade() -> None:
    """Откат: удаление таблицы валют"""
    op.drop_table('currency')