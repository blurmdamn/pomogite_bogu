from datetime import datetime
from pydantic import BaseModel, Field
from typing_extensions import Optional


class ProductCreate(BaseModel):
    """
    Схема добавления продукта в список желаемого.
    """
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    wishlist_id: int


class ShowProduct(BaseModel):
    """
    Схема отображения информации о продукте.
    """
    id: int
    name: str
    price: float
    wishlist_id: int
    created_at: datetime

    class ConfigDict:
        from_attributes = True


class UpdateProduct(BaseModel):
    """
    Схема обновления продукта.
    """
    name: Optional[str] = None
    price: Optional[float] = None
