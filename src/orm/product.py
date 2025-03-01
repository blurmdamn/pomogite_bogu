from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product


async def add_product_to_wishlist(product_data: dict, async_db: AsyncSession):
    """
    Добавить продукт в список желаемого.
    """
    product = Product(**product_data)
    async_db.add(product)
    await async_db.commit()
    return product


async def list_products_by_wishlist(wishlist_id: int, async_db: AsyncSession):
    """
    Получить список продуктов для определенного списка желаемого.
    """
    query = select(Product).where(Product.wishlist_id == wishlist_id)
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
