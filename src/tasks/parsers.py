from celery import shared_task
import asyncio
from src.parsers.steam_parser import main as steam_main
from src.parsers.gog_parser import main as gog_main
from src.parsers.nintendo_parser import main as nintendo_main

@shared_task
def run_steam_parser():
    asyncio.run(steam_main())

@shared_task
def run_gog_parser():
    asyncio.run(gog_main())

@shared_task
def run_nintendo_parser():
    asyncio.run(nintendo_main())
