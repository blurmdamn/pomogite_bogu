"""Add currency_id to products

Revision ID: 148502fb0586
Revises: 8885bf95436f
Create Date: 2025-03-23 17:26:03.249445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '148502fb0586'
down_revision: Union[str, None] = '8885bf95436f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Добавляем временную колонку currency_id (nullable)
    op.add_column('products', sa.Column('currency_id', sa.Integer(), nullable=True))
    
    # 2. Заполняем currency_id нужными значениями:
    # Для магазина Steam устанавливаем валюту KZT
    op.execute(
        """
        UPDATE products
        SET currency_id = (
            SELECT id FROM currency WHERE name = 'KZT'
        )
        WHERE store_id IN (
            SELECT id FROM stores WHERE name = 'Steam'
        )
        """
    )
    # Для магазинов GOG и Nintendo Store устанавливаем валюту USD
    op.execute(
        """
        UPDATE products
        SET currency_id = (
            SELECT id FROM currency WHERE name = 'USD'
        )
        WHERE store_id IN (
            SELECT id FROM stores WHERE name IN ('GOG', 'Nintendo Store')
        )
        """
    )
    
    # 3. Делаем колонку NOT NULL
    op.alter_column('products', 'currency_id', nullable=False)
    
    # 4. Создаем индекс и внешний ключ
    op.create_index(op.f('ix_products_currency_id'), 'products', ['currency_id'], unique=False)
    op.create_foreign_key(None, 'products', 'currency', ['currency_id'], ['id'])
    
    # 5. Удаляем старое поле currency
    op.drop_column('products', 'currency')

def downgrade() -> None:
    # Вариант отката: добавляем старое поле currency, удаляем новый внешний ключ и колонку currency_id
    op.add_column('products', sa.Column('currency', sa.VARCHAR(length=10), nullable=True))
    op.drop_constraint(None, 'products', type_='foreignkey')
    op.drop_index(op.f('ix_products_currency_id'), table_name='products')
    op.drop_column('products', 'currency_id')