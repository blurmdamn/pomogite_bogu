import asyncio
import logging

from sqlalchemy import select, update, func
from src.database import async_session_maker
from src.models.products import Product
from src.models.stores import Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def update_search_vector():
    async with async_session_maker() as session:
        # Получаем магазины
        steam_store = await session.scalar(select(Store).where(Store.name == "Steam"))
        gog_store = await session.scalar(select(Store).where(Store.name == "GOG"))

        if not steam_store or not gog_store:
            logging.error("❌ Не найдены магазины Steam или GOG в базе данных.")
            return

        # Обновление для Steam (используем русский анализатор)
        await session.execute(
            update(Product)
            .where(Product.store_id == steam_store.id)
            .values(
                search_vector=func.to_tsvector("russian", Product.description)
            )
        )
        logging.info("✅ Обновлены Steam search_vector")

        # Обновление для GOG (используем английский анализатор)
        await session.execute(
            update(Product)
            .where(Product.store_id == gog_store.id)
            .values(
                search_vector=func.to_tsvector("english", Product.description)
            )
        )
        logging.info("✅ Обновлены GOG search_vector")

        await session.commit()
        logging.info("🎉 Коммит завершен")


if __name__ == "__main__":
    asyncio.run(update_search_vector())
