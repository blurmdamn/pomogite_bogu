from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.models.products import Product
from src.models.wishlists_products import wishlist_product
from src.orm.store import get_store_by_name



async def add_product_to_wishlist(product_data: dict, async_db: AsyncSession):
    """
    Добавить продукт в список желаемого.
    """
    # Проверяем, существует ли магазин
    store = await get_store_by_name(product_data["store_name"], async_db)
    if not store:
        raise ValueError(f"Магазин '{product_data['store_name']}' не найден")

    product_data["store_id"] = store.id
    product_data.pop("store_name", None)
    product_data.pop("currency_name", None)

    product = Product(**product_data)
    async_db.add(product)

    try:
        await async_db.commit()
        await async_db.refresh(product)
    except IntegrityError:
        await async_db.rollback()
        raise ValueError("Ошибка при добавлении продукта. Возможно, такой продукт уже существует.")

    return product


async def list_products_by_wishlist(wishlist_id: int, async_db: AsyncSession):
    """
    Получить список продуктов для определенного списка желаемого.
    """
    query = select(Product).join(wishlist_product).where(wishlist_product.c.wishlist_id == wishlist_id)
    result = await async_db.execute(query)
    return result.scalars().all()


async def update_product_price(product_id: int, new_price: float, async_db: AsyncSession):
    """
    Обновить цену продукта.
    """
    query = update(Product).where(Product.id == product_id).values(price=new_price).returning(Product)
    result = await async_db.execute(query)
    await async_db.commit()
    return result.scalar()


async def delete_product(product_id: int, async_db: AsyncSession):
    """
    Удалить продукт.
    """
    query = delete(Product).where(Product.id == product_id)
    result = await async_db.execute(query.execution_options(synchronize_session="fetch"))
    await async_db.commit()
    return result.rowcount > 0
