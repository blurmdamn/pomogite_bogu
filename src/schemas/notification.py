from datetime import datetime
from pydantic import BaseModel, Field
from typing_extensions import Optional


class NotificationCreate(BaseModel):
    """
    Схема создания уведомления.
    """
    message: str = Field(..., min_length=1)
    user_id: int
    product_id: int


class ShowNotification(BaseModel):
    """
    Схема отображения уведомления.
    """
    id: int
    message: str
    user_id: int
    product_id: int
    created_at: datetime

    class ConfigDict:
        from_attributes = True
