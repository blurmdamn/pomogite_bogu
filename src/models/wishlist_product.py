from sqlalchemy import Table, Column, ForeignKey
from src.models.base_class import Base

wishlist_product = Table(
    "wishlist_product",
    Base.metadata,
    Column("wishlist_id", ForeignKey("wishlist.id"), primary_key=True),
    Column("product_id", ForeignKey("product.id"), primary_key=True),
)
