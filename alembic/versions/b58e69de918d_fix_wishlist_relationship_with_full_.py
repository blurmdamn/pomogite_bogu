"""Fix Wishlist relationship with full module path

Revision ID: b58e69de918d
Revises: 0b79c49c8fdd
Create Date: 2025-03-01 20:54:11.156695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b58e69de918d'
down_revision: Union[str, None] = '0b79c49c8fdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
