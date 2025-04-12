from datetime import datetime
from pydantic import BaseModel
from typing_extensions import Optional
from typing import List
from src.schemas.product import ShowProduct  # обязательно должен существовать!
from src.schemas.product import ShowProductWithStore


class WishlistCreate(BaseModel):
    """
    Схема создания нового списка желаемого.
    """
    name: Optional[str] = None  # Пользователь может дать название списку


class ShowWishlist(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    products: List[ShowProductWithStore] = []  # 👈 добавили список продуктов

    class ConfigDict:
        from_attributes = True

class WishlistAddProduct(BaseModel):
    """
    Схема для добавления продукта в вишлист
    """
    product_id: int
