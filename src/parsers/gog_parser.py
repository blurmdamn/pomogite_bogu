import logging
import asyncio
import re
import json
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, select

from src.config import prod_db_settings
from src.models.products import Product
from src.models.stores import Store

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Настройка подключения к БД
DATABASE_URL = prod_db_settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def clean_price(price_text: str) -> float:
    """Форматирует цену в число с плавающей точкой."""
    if not price_text or price_text.lower() in ["free", "бесплатно"]:
        return 0.0

    price_text = re.sub(r"\s+", "", price_text, flags=re.UNICODE)
    cleaned = re.sub(r"[^\d,\.]", "", price_text)

    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    return float(cleaned) if re.match(r"^\d+(\.\d+)?$", cleaned) else 0.0


class GOGParser:
    BASE_URL = "https://www.gog.com/ru/games?page={}"

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
        logging.info("Selenium WebDriver initialized.")

    def fetch_data(self, pages: int = 208) -> list:
        results = []

        for page in range(1, pages + 1):
            url = self.BASE_URL.format(page)
            logging.info("📄 Fetching page %d: %s", page, url)

            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="Catalog"]')))

            a_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a.product-tile')

            for i in range(1, 49):
                base_xpath = f'//*[@id="Catalog"]/div/div[2]/paginated-products-grid/div/product-tile[{i}]'
                title_xpath = f'{base_xpath}/a/div[2]/div[1]/product-title/span'

                # 🔧 Обновлённый блок для поиска цены
                price_xpath_final = f'{base_xpath}//span[contains(@class, "final-value")]'
                price_xpath_base = f'{base_xpath}//span[contains(@class, "base-value")]'

                title_elements = self.driver.find_elements(By.XPATH, title_xpath)
                price_elements = self.driver.find_elements(By.XPATH, price_xpath_final)
                if not price_elements:
                    price_elements = self.driver.find_elements(By.XPATH, price_xpath_base)

                if title_elements and i - 1 < len(a_elements):
                    title = title_elements[0].text.strip()
                    price_raw = price_elements[0].get_attribute("textContent").strip() if price_elements else ""
                    price = clean_price(price_raw)
                    game_url = a_elements[i - 1].get_attribute("href")

                    results.append({
                        "title": title,
                        "price": price,
                        "url": game_url,
                    })

                    logging.info("✅ Parsed game: %s | Price: %s | URL: %s", title, price, game_url)
                else:
                    logging.info("⛔️ No title or URL found for product %d on page %d", i, page)

        logging.info("🎯 Total games parsed: %d", len(results))
        return results

    def close(self):
        self.driver.quit()
        logging.info("Selenium WebDriver closed.")


async def get_or_create_store(session: AsyncSession) -> Store:
    result = await session.execute(select(Store).where(Store.name == "GOG"))
    store = result.scalars().first()
    if not store:
        store = Store(name="GOG", url="https://www.gog.com/ru/games")
        session.add(store)
        await session.commit()
        await session.refresh(store)
        logging.info("Store 'GOG' created in DB.")
    else:
        logging.info("Store 'GOG' already exists in DB.")
    return store


async def save_to_db(data: list):
    async with SessionLocal() as session:
        store = await get_or_create_store(session)
        new_count = 0
        updated_count = 0

        for item in data:
            price = float(item["price"])

            res = await session.execute(
                select(Product).where(
                    and_(
                        Product.name == item["title"],
                        Product.store_id == store.id
                    )
                )
            )
            product = res.scalars().first()
            if product:
                product.price = price
                updated_count += 1
            else:
                new_product = Product(
                    name=item["title"],
                    price=price,
                    url=item["url"],
                    store_id=store.id
                )
                session.add(new_product)
                new_count += 1

        logging.info("🆕 New: %d | 🔄 Updated: %d", new_count, updated_count)
        await session.commit()
        logging.info("✅ Database commit successful.")


async def main():
    parser = GOGParser(headless=True)
    logging.info("🚀 Starting GOG parser...")
    data = parser.fetch_data(pages=208)

    if data:
        await save_to_db(data)
    else:
        logging.warning("⚠️ No data parsed from GOG.")

    parser.close()
