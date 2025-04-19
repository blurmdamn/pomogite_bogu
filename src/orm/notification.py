from sqlalchemy.future import select  # ✅ это правильный SQLAlchemy-импорт
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.models.notifications import Notification


async def create_notification(notification_data: dict, async_db: AsyncSession):
    """
    Создать новое уведомление.
    """
    notification = Notification(**notification_data)
    async_db.add(notification)

    try:
        await async_db.commit()
        await async_db.refresh(notification)
    except IntegrityError:
        await async_db.rollback()
        raise ValueError("Ошибка при создании уведомления.")

    return notification


async def list_notifications_by_user(user_id: int, async_db: AsyncSession):
    """
    Получить все уведомления пользователя.
    """
    query = select(Notification).where(Notification.user_id == user_id)
    result = await async_db.execute(query)
    return result.scalars().all()


from sqlalchemy import update
from src.models.notifications import Notification

async def mark_all_notifications_as_read(user_id: int, async_db: AsyncSession):
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await async_db.execute(stmt)
    await async_db.commit()
