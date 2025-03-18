from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_class import Base

if TYPE_CHECKING:
    from .wishlists import Wishlist
    from .notifications import Notification

class User(Base):
    __tablename__ = "users"  # Название таблицы во множественном числе

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    wishlists: Mapped[list["Wishlist"]] = relationship("Wishlist", back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user")
