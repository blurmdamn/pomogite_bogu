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
    description="Получение списка уведомлений текущего пользователя",
)
async def list_notifications(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user)
):
    return await notification_orm.list_notifications_by_user(user_id=current_user.id, async_db=db)


@api_router.post(
    "/mark_all_as_read",
    status_code=status.HTTP_200_OK,
    description="Пометить все уведомления как прочитанные"
)
async def mark_all_as_read(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user)
):
    await notification_orm.mark_all_notifications_as_read(user_id=current_user.id, async_db=db)
    return {"message": "Все уведомления помечены как прочитанные"}
