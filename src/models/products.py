from typing import TYPE_CHECKING, Optional
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import ForeignKey, Integer, String, Float, TIMESTAMP, func, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_class import Base
from .wishlists_products import wishlist_product

if TYPE_CHECKING:
    from .stores import Store
    from .wishlists import Wishlist

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)

    # 🆕 Добавленные поля
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enriched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR)

    store: Mapped["Store"] = relationship("Store", back_populates="products", lazy="joined")
    wishlists: Mapped[list["Wishlist"]] = relationship("Wishlist", secondary=wishlist_product, back_populates="products")
    
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
