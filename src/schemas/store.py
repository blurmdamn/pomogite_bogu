from pydantic import BaseModel, Field
from typing_extensions import Optional


class StoreCreate(BaseModel):
    """
    Схема создания нового магазина.
    """
    name: str = Field(..., min_length=1)
    url: str = Field(..., pattern=r'^https?://[^\s/$.?#].[^\s]*$')  # ✅ правильный синтаксис



class ShowStore(BaseModel):
    """
    Схема отображения информации о магазине.
    """
    id: int
    name: str
    url: str

    class ConfigDict:
        from_attributes = True
