from psycopg2 import IntegrityError
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.wishlists import Wishlist


async def create_wishlist(user_id: int, async_db: AsyncSession):
    """
    Создать новый список желаемого.
    """
    wishlist = Wishlist(user_id=user_id)
    async_db.add(wishlist)

    try:
        await async_db.commit()
        await async_db.refresh(wishlist)
    except IntegrityError:
        await async_db.rollback()
        raise ValueError("Ошибка при создании списка желаемого.")

    return wishlist


async def list_wishlists_by_user(user_id: int, async_db: AsyncSession):
    """
    Получить списки желаемого пользователя.
    """
    query = select(Wishlist).where(Wishlist.user_id == user_id)
    result = await async_db.execute(query)
    return result.scalars().all()


async def delete_wishlist(wishlist_id: int, async_db: AsyncSession):
    """
    Удалить список желаемого.
    """
    query = delete(Wishlist).where(Wishlist.id == wishlist_id)
    result = await async_db.execute(query.execution_options(synchronize_session="fetch"))
    await async_db.commit()
    return result.rowcount > 0
