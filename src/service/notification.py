from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.notification import NotificationCreate
from src.orm.notification import create_notification

# позже сюда добавим send_telegram_notification()

async def send_notification(notification_data: NotificationCreate, db: AsyncSession):
    """
    Отправить уведомление:
    - сохранить в БД
    - отправить в Telegram (опционально)
    """
    # Сохраняем в БД
    await create_notification(notification_data.dict(), db)

    # TODO: если подключён Telegram-бот — вызвать здесь send_telegram_notification
    # await send_telegram_notification(user_id=notification_data.user_id, message=notification_data.message)
