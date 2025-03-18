from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_class import Base
from .wishlists_products import wishlist_product

if TYPE_CHECKING:
    from .users import User
    from .products import Product

class Wishlist(Base):
    __tablename__ = "wishlists"  # Название таблицы во множественном числе

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Обновлённое имя таблицы

    user: Mapped["User"] = relationship("User", back_populates="wishlists")
    products: Mapped[list["Product"]] = relationship("Product", secondary=wishlist_product, back_populates="wishlists")
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
