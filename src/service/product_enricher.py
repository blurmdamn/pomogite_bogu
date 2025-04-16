import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from src.database import async_session_maker
from src.models.products import Product
from src.models.stores import Store

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DescriptionEnricher:
    def __init__(self, headless: bool = True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("🔧 Selenium WebDriver initialized.")

    def fetch_steam_description(self, url: str) -> str | None:
        try:
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.ID, "game_area_description")))
            element = self.driver.find_element(By.ID, "game_area_description")
            return element.text.strip()
        except Exception as e:
            logging.warning(f"❌ Failed to fetch Steam description: {url} | {e}")
            return None

    def fetch_gog_description(self, url: str) -> str | None:
        try:
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "description")))
            element = self.driver.find_element(By.CLASS_NAME, "description")
            return element.text.strip()
        except Exception as e:
            logging.warning(f"❌ Failed to fetch GOG description: {url} | {e}")
            return None

    def close(self):
        self.driver.quit()
        logging.info("🛑 Selenium WebDriver closed.")


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
        enricher = DescriptionEnricher(headless=True)

        for product in products:
            description = enricher.fetch_gog_description(product.url)
            if description:
                product.description = description
                product.is_enriched = True
                logging.info(f"✅ GOG enriched: {product.name}")
            else:
                logging.warning(f"⚠️ GOG skipped: {product.name}")

        await session.commit()
        enricher.close()
        logging.info("🎉 GOG enrichment done.")


async def enrich_steam_products():
    async with async_session_maker() as session:
        steam_store = await session.scalar(select(Store).where(Store.name == "Steam"))
        if not steam_store:
            logging.error("❌ Steam store not found in DB.")
            return

        products = await session.scalars(
            select(Product).where(
                Product.store_id == steam_store.id,
                Product.is_enriched.is_(False),
                Product.description.is_(None),
                Product.url.like('%store.steampowered.com/app/%')
            )
        )
        products = products.all()

        logging.info(f"🧠 Found {len(products)} Steam products to enrich.")
        enricher = DescriptionEnricher(headless=True)

        for product in products:
            description = enricher.fetch_steam_description(product.url)
            if description:
                product.description = description
                product.is_enriched = True
                logging.info(f"✅ Steam enriched: {product.name}")
            else:
                logging.warning(f"⚠️ Steam skipped: {product.name}")

        await session.commit()
        enricher.close()
        logging.info("🎉 Steam enrichment done.")


if __name__ == "__main__":
    asyncio.run(enrich_gog_products())
    asyncio.run(enrich_steam_products())
