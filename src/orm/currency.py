from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.currency import Currency


async def get_currency_by_name(name: str, async_db: AsyncSession):
    """
    Получить валюту по названию (например, "KZT" или "USD").
    """
    query = select(Currency).where(Currency.name == name)
    result = await async_db.execute(query)
    return result.scalar_one_or_none()
