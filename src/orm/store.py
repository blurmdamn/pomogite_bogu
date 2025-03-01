from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.store import Store


async def get_store_by_name(store_name: str, async_db: AsyncSession):
    """
    Получить магазин по названию.
    """
    query = select(Store).where(Store.name == store_name)
    result = await async_db.execute(query)
    return result.scalar()


async def list_all_stores(async_db: AsyncSession):
    """
    Получить список всех магазинов.
    """
    query = select(Store)
    result = await async_db.execute(query)
    return result.scalars().all()
