from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from src.config import prod_db_settings

# Создаем асинхронный движок для работы с PostgreSQL через asyncpg
engine = create_async_engine(
    prod_db_settings.DATABASE_URL, 
    echo=True,  # Логирование запросов (можно отключить в продакшене)
    future=True
)

# Фабрика сессий для асинхронных операций
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """ Асинхронный генератор для получения сессии базы данных. """
    async with async_session_maker() as session:
        yield session
