"""Insert initial currencies

Revision ID: 8885bf95436f
Revises: d8975cbcf4de
Create Date: 2025-03-23 08:44:34.281638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8885bf95436f'
down_revision: Union[str, None] = 'd8975cbcf4de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет стандартные валюты в таблицу currency"""
    op.execute(
        """
        INSERT INTO currency (name, symbol) VALUES
        ('USD', '$'),
        ('EUR', '€'),
        ('KZT', '₸'),
        ('RUB', '₽');
        """
    )


def downgrade() -> None:
    """Откат: удаляет добавленные валюты"""
    op.execute(
        """
        DELETE FROM currency WHERE name IN ('USD', 'EUR', 'KZT', 'RUB', 'GBP');
        """
    )