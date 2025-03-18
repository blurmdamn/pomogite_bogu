from sqlalchemy import Table, Column, ForeignKey
from src.models.base_class import Base

wishlist_product = Table(
    "wishlists_products",  # Обновленное имя таблицы во множественном числе
    Base.metadata,
    Column("wishlist_id", ForeignKey("wishlists.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)
