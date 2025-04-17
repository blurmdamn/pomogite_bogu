from sqlalchemy import select, delete, update, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from src.models.products import Product
from src.models.wishlists_products import wishlist_product
from src.models.stores import Store
from src.orm.store import get_store_by_name


# 🟩 Добавление нового продукта в wishlist
async def add_product_to_wishlist(product_data: dict, async_db: AsyncSession):
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


# 🟨 Список продуктов по wishlist
async def list_products_by_wishlist(wishlist_id: int, async_db: AsyncSession):
    query = select(Product).join(wishlist_product).where(wishlist_product.c.wishlist_id == wishlist_id)
    result = await async_db.execute(query)
    return result.scalars().all()


# 🟧 Обновление цены продукта
async def update_product_price(product_id: int, new_price: float, async_db: AsyncSession):
    query = update(Product).where(Product.id == product_id).values(price=new_price).returning(Product)
    result = await async_db.execute(query)
    await async_db.commit()
    return result.scalar()


# 🟥 Удаление продукта
async def delete_product(product_id: int, async_db: AsyncSession):
    query = delete(Product).where(Product.id == product_id)
    result = await async_db.execute(query.execution_options(synchronize_session="fetch"))
    await async_db.commit()
    return result.rowcount > 0


# 🔍 Поиск по названию через полнотекстовый поиск
async def search_products(query: str, async_db):
    # Построение TS-запросов для Steam и GOG
    steam_ts = func.plainto_tsquery("russian", query)
    gog_ts = func.plainto_tsquery("english", query)

    stmt = (
        select(Product)
        .join(Store)
        .where(
            or_(
                # FTS для Steam
                and_(
                    Store.name == "Steam",
                    Product.search_vector.op('@@')(steam_ts)
                ),
                # FTS для GOG
                and_(
                    Store.name == "GOG",
                    Product.search_vector.op('@@')(gog_ts)
                ),
                # ILIKE для остальных магазинов (например, Nintendo)
                Product.name.ilike(f"%{query}%")
            )
        )
        .options(joinedload(Product.store))
        .limit(20)
    )

    result = await async_db.execute(stmt)
    return result.scalars().all()

# 🤖 Умный поиск по описанию с сортировкой по релевантности
async def smart_search_products(query: str, async_db: AsyncSession):
    steam_ts = func.plainto_tsquery("russian", query)
    gog_ts = func.plainto_tsquery("english", query)

    stmt = (
        select(Product, func.ts_rank(Product.search_vector, steam_ts).label("rank"))
        .join(Store)
        .where(
            or_(
                and_(Store.name == "Steam", Product.search_vector.op('@@')(steam_ts)),
                and_(Store.name == "GOG", Product.search_vector.op('@@')(gog_ts)),
            )
        )
        .options(joinedload(Product.store))
        .order_by(func.ts_rank(Product.search_vector, steam_ts).desc())
        .limit(20)
    )

    result = await async_db.execute(stmt)
    products = [row[0] for row in result.all()]  # Извлекаем Product из кортежей
    return products


async def get_all_products(async_db: AsyncSession):
    query = select(Product).options(joinedload(Product.store)).order_by(Product.created_at.desc()).limit(100)
    result = await async_db.execute(query)
    return result.scalars().all()

async def get_products_by_store(store_name: str, async_db: AsyncSession):
    stmt = (
        select(Product)
        .join(Store)
        .where(Store.name.ilike(store_name))  # нечувствительно к регистру
        .options(joinedload(Product.store))
        .order_by(Product.created_at.desc())
    )
    result = await async_db.execute(stmt)
    return result.scalars().all()
