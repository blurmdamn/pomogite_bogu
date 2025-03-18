from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.notifications import Notification


async def create_notification(notification_data: dict, async_db: AsyncSession):
    """
    Создать новое уведомление.
    """
    query = insert(Notification).values(**notification_data).returning(Notification)
    result = await async_db.execute(query)
    await async_db.commit()
    return result.scalar()


async def list_notifications_by_user(user_id: int, async_db: AsyncSession):
    """
    Получить все уведомления пользователя.
    """
    query = select(Notification).where(Notification.user_id == user_id)
    result = await async_db.execute(query)
    return result.scalars().all()
