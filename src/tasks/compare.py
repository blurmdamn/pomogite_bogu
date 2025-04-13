from src.celery import celery_app
from src.database import async_session_maker
from src.service.compare import find_and_notify_cheaper_games

@celery_app.task
def compare_prices_and_notify():
    import asyncio

    async def inner():
        async with async_session_maker() as session:
            await find_and_notify_cheaper_games(session)

    asyncio.run(inner())
