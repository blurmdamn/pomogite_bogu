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


from sqlalchemy.orm import joinedload

async def list_wishlists_by_user(user_id: int, async_db: AsyncSession):
    """
    Получить списки желаемого пользователя с предзагрузкой продуктов.
    """
    query = (
        select(Wishlist)
        .where(Wishlist.user_id == user_id)
        .options(joinedload(Wishlist.products))  # предзагрузка игр
    )
    result = await async_db.execute(query)
    return result.unique().scalars().all()



async def delete_wishlist(wishlist_id: int, async_db: AsyncSession):
    """
    Удалить список желаемого.
    """
    query = delete(Wishlist).where(Wishlist.id == wishlist_id)
    result = await async_db.execute(query.execution_options(synchronize_session="fetch"))
    await async_db.commit()
    return result.rowcount > 0


from sqlalchemy import select
from src.models.wishlists import Wishlist

async def get_or_create_user_wishlist(async_db: AsyncSession, user_id: int):
    result = await async_db.execute(
        select(Wishlist).where(Wishlist.user_id == user_id)
    )
    wishlist = result.scalars().first()

    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        async_db.add(wishlist)
        await async_db.commit()
        await async_db.refresh(wishlist)

    return wishlist


from sqlalchemy.dialects.postgresql import insert
from src.models.wishlists_products import wishlist_product

async def add_product_to_wishlist(async_db: AsyncSession, wishlist_id: int, product_id: int):
    stmt = insert(wishlist_product).values(
        wishlist_id=wishlist_id, product_id=product_id
    ).on_conflict_do_nothing()
    await async_db.execute(stmt)
    await async_db.commit()

async def add_product_to_user_wishlist(user_id: int, product_id: int, async_db: AsyncSession):
    wishlist = await get_or_create_user_wishlist(async_db, user_id)
    await add_product_to_wishlist(async_db, wishlist.id, product_id)
    return {"message": "Product added to wishlist"}


from sqlalchemy.orm import joinedload
from sqlalchemy import select
from src.models.wishlists import Wishlist

async def list_wishlists(async_db: AsyncSession):
    result = await async_db.execute(
        select(Wishlist).options(joinedload(Wishlist.products))
    )
    return result.scalars().all()
