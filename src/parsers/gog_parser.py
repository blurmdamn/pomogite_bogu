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
    """Форматирует цену."""
    if not price_text or price_text.lower() in ["free", "бесплатно"]:
        return 0.0
    cleaned = re.sub(r"[^\d,\.]", "", price_text)
    cleaned = cleaned.replace(" ", "").replace(",", ".")
    return float(cleaned)


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

    def fetch_data(self, pages: int = 209) -> list:
        results = []
        for page in range(1, pages + 1):
            url = self.BASE_URL.format(page)
            logging.info("Fetching page %d: %s", page, url)
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="Catalog"]')))
            for i in range(1, 49):
                title_xpath = f'//*[@id="Catalog"]/div/div[2]/paginated-products-grid/div/product-tile[{i}]/a/div[2]/div[1]/product-title/span'
                price_xpath = f'//*[@id="Catalog"]/div/div[2]/paginated-products-grid/div/product-tile[{i}]/a/div[2]/div[2]/div/product-price/price-value/span'
                title_elements = self.driver.find_elements(By.XPATH, title_xpath)
                price_elements = self.driver.find_elements(By.XPATH, price_xpath)
                if title_elements:
                    title = title_elements[0].text.strip()
                    price_text = price_elements[0].text.strip() if price_elements else ""
                    price = clean_price(price_text)
                    results.append({"title": title, "price": price, "url": url})
                    logging.info("Parsed game: %s | Price: %s", title, price)
                else:
                    logging.info("No title found for product %d on page %d", i, page)
        logging.info("Parsed %d games.", len(results))
        return results

    def save_to_json(self, data: list, filename: str = "gog_games.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info("Data saved to JSON file: %s", filename)

    def save_to_csv(self, data: list, filename: str = "gog_games.csv"):
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Название", "Цена", "URL"])
            for item in data:
                writer.writerow([item["title"], item["price"], item["url"]])
        logging.info("Data saved to CSV file: %s", filename)

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
        logging.info("SSSSSSSSSSSSSS: ", data)

        for item in data:
            price = float(item["price"])  # Предполагается, что clean_price уже всё обработал

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

        logging.info("Ready to commit. New: %d, Updated: %d", new_count, updated_count)
        await session.commit()
        logging.info("Database commit successful.")


async def main():
    parser = GOGParser(headless=True)
    logging.info("testttt")
    data = parser.fetch_data(pages=209)
    print("test")
    logging.info("FFFFFFFD:  ", data)
    if data:
        # parser.save_to_json(data)
        # parser.save_to_csv(data)
        await save_to_db(data)
    else:
        logging.warning("No data parsed from GOG.")
    parser.close()


# if __name__ == "__main__":
#     asyncio.run(main())
