from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from src.models.users import User

async def update_telegram_id(user_id: int, telegram_id: int, db: AsyncSession):
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(telegram_id=telegram_id)
    )
    await db.commit()
