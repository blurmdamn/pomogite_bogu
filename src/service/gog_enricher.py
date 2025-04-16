import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from src.database import async_session_maker
from src.models.products import Product
from src.models.stores import Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_gog_description_bs4(url: str) -> str | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        desc_div = soup.find("div", class_="description")
        if not desc_div:
            logging.warning(f"❌ Description block not found at {url}")
            return None

        copyright_tag = desc_div.find("p", class_="description__copyrights")
        if copyright_tag:
            copyright_tag.decompose()

        return desc_div.get_text(strip=True)
    except Exception as e:
        logging.warning(f"❌ Failed to fetch GOG description via BS4: {url} | {e}")
        return None


async def enrich_gog_products():
    async with async_session_maker() as session:
        gog_store = await session.scalar(select(Store).where(Store.name == "GOG"))
        if not gog_store:
            logging.error("❌ GOG store not found in DB.")
            return

        products = await session.scalars(
            select(Product).where(
                Product.store_id == gog_store.id,
                Product.is_enriched.is_(False),
                Product.description.is_(None),
                Product.url.like('%/game/%')
            )
        )
        products = products.all()

        logging.info(f"🧠 Found {len(products)} GOG products to enrich.")

        enriched = 0
        for product in products:
            description = fetch_gog_description_bs4(product.url)
            if description:
                product.description = description
                product.is_enriched = True
                enriched += 1
                logging.info(f"✅ Enriched: {product.name}")
            else:
                logging.warning(f"⚠️ Skipped: {product.name}")

        await session.commit()
        logging.info(f"🎉 Enrichment complete. Total enriched: {enriched}")


if __name__ == "__main__":
    asyncio.run(enrich_gog_products())
