# pomogite_bogu
 uvicorn src.main:app --reload
 rm -rf alembic/versions/*    
 alembic upgrade head       
 alembic revision --autogenerate -m "Initial migration"


git add .

git commit -m "Commit"

 git push origin master


celery -A src.celery.worker.celery_app worker --loglevel=info


celery -A src.celery.worker call src.tasks.parsers.run_gog_parser #для задач
celery -A src.celery.worker call src.tasks.compare.compare_prices_and_notify



import asyncio
from src.database import async_session_maker
from src.service.compare import find_and_notify_cheaper_games

async def test():
    async with async_session_maker() as session:
        await find_and_notify_cheaper_games(session)

asyncio.run(test())



python -m src.service.gog_enricher

python -m src.service.steam_enricher

python -m src.scripts.update_search_vector