from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session
from src.schemas.notification import NotificationCreate, ShowNotification
from src.orm import notification as notification_orm
from src.service.auth import get_current_user

api_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@api_router.post(
    "/create/",
    response_model=ShowNotification,
    status_code=status.HTTP_201_CREATED,
    description="Создание нового уведомления",
)
async def create_notification(
    notification: NotificationCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    return await notification_orm.create_new_notification(
        notification_schema=notification, async_db=db, user_id=current_user.id
    )


@api_router.get(
    "/list/",
    response_model=List[ShowNotification],
    status_code=status.HTTP_200_OK,
    description="Получение списка уведомлений",
)
async def list_notifications(db: AsyncSession = Depends(get_async_session)):
    return await notification_orm.list_notifications(async_db=db)
