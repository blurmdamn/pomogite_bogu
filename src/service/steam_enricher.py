import asyncio
import logging
import requests
from bs4 import BeautifulSoup

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


class SteamDescriptionEnricher:
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
        logging.info("🟢 Selenium WebDriver initialized.")

    def fetch_steam_description(self, url: str) -> str | None:
        try:
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.ID, "game_area_description")))
            element = self.driver.find_element(By.ID, "game_area_description")
            return element.text.strip()
        except Exception as e:
            logging.warning(f"⚠️ Selenium failed for: {url} | {e}")
            # fallback через requests
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    desc_block = soup.find(id="game_area_description")
                    if desc_block:
                        return desc_block.get_text(strip=True)
                    else:
                        logging.warning(f"❌ No #game_area_description found via requests for {url}")
                else:
                    logging.warning(f"❌ Requests failed, status {response.status_code} for {url}")
            except Exception as r_err:
                logging.warning(f"❌ Requests fallback failed for {url} | {r_err}")

            return None

    def close(self):
        self.driver.quit()
        logging.info("🔴 Selenium WebDriver closed.")


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
        enricher = SteamDescriptionEnricher(headless=True)

        for product in products:
            description = enricher.fetch_steam_description(product.url)
            if description:
                product.description = description
                product.is_enriched = True
                logging.info(f"✅ Enriched: {product.name}")
            else:
                logging.warning(f"⚠️ Skipped: {product.name}")

        await session.commit()
        enricher.close()
        logging.info("🎉 Steam enrichment complete.")


if __name__ == "__main__":
    asyncio.run(enrich_steam_products())
