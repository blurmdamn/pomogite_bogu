"""Rename tables to plural

Revision ID: e3a27b8b851d
Revises: effc149b02ec
Create Date: 2025-03-11 14:36:16.508745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3a27b8b851d'
down_revision: Union[str, None] = 'effc149b02ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.rename_table('store', 'stores')
    op.rename_table('product', 'products')
    op.rename_table('user', 'users')
    op.rename_table('wishlist', 'wishlists')
    op.rename_table('wishlist_product', 'wishlists_products')
    op.rename_table('notification', 'notifications')


def downgrade():
    op.rename_table('stores', 'store')
    op.rename_table('products', 'product')
    op.rename_table('users', 'user')
    op.rename_table('wishlists', 'wishlist')
    op.rename_table('wishlists_products', 'wishlist_product')
    op.rename_table('notifications', 'notification')
