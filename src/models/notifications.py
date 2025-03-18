from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_class import Base

if TYPE_CHECKING:
    from .users import User

class Notification(Base):
    __tablename__ = "notifications"  # Название таблицы во множественном числе

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Обновлённое имя таблицы
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")
