from pydantic import BaseModel, Field
from typing_extensions import Optional


class UserCreate(BaseModel):
    """
    Схема создания нового пользователя.
    """
    username: str = Field(..., min_length=3, max_length=30)
    email: str = Field(..., pattern=r'^\S+@\S+\.\S+$')
    password: str = Field(..., min_length=8)


class ShowUser(BaseModel):
    """
    Схема отображения информации о пользователе.
    """
    id: int
    username: str
    email: str
    is_active: bool
    telegram_id: Optional[int] = None  # 👈 добавить

    class ConfigDict:
        from_attributes = True


class UpdateUser(BaseModel):
    """
    Схема обновления информации о пользователе.
    """
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UpdateTelegramID(BaseModel):
    """
    Схема для обновления Telegram ID пользователя.
    """
    user_id: int
    telegram_id: int
