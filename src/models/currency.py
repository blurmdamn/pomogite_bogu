from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_class import Base

class Currency(Base):
    __tablename__ = "currency"
    __table_args__ = {"extend_existing": True}  # чтобы переопределять, если таблица уже определена

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # например, "KZT", "USD"
    symbol: Mapped[str] = mapped_column(String, nullable=False)  # например, "₸", "$"

    products = relationship("Product", back_populates="currency")
