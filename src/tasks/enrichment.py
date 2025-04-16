from celery import shared_task
import asyncio

from src.service.gog_enricher import enrich_gog_products
from src.service.steam_enricher import enrich_steam_products

@shared_task(name="tasks.enrich_gog_products")
def run_gog_enrichment():
    asyncio.run(enrich_gog_products())

@shared_task(name="tasks.enrich_steam_products")
def run_steam_enrichment():
    asyncio.run(enrich_steam_products())
