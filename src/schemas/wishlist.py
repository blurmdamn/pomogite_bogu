from datetime import datetime
from pydantic import BaseModel
from typing_extensions import Optional


class WishlistCreate(BaseModel):
    """
    Схема создания нового списка желаемого.
    """
    name: Optional[str] = None  # Пользователь может дать название списку


class ShowWishlist(BaseModel):
    """
    Схема отображения списка желаемого.
    """
    id: int
    name: Optional[str]
    user_id: int
    created_at: datetime

    class ConfigDict:
        from_attributes = True
