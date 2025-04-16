from celery import shared_task
import asyncio

from src.scripts.update_search_vector import update_search_vector

@shared_task(name="tasks.update_search_vector")
def run_search_vector_update():
    asyncio.run(update_search_vector())
