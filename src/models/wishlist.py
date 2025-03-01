from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_class import Base
from .wishlist_product import wishlist_product

if TYPE_CHECKING:
    from .user import User
    from .product import Product

class Wishlist(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    # Используем просто "User", поскольку в реестре зарегистрирован класс с именем "User"
    user: Mapped["User"] = relationship("User", back_populates="wishlists")
    
    products: Mapped[list["Product"]] = relationship(
        "Product", secondary=wishlist_product, back_populates="wishlists"
    )
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
