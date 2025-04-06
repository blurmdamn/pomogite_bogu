import logging
import asyncio
import re
import json
import csv
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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


class NintendoParser:
    BASE_URL = "https://www.nintendo.com/us/store/games/best-sellers/#sort=df&p={}"

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

    def scroll_page(self):
        """Прокручивает страницу вниз, чтобы подгрузить контент."""
        body = self.driver.find_element(By.TAG_NAME, "body")
        for _ in range(10):  # Прокручиваем 10 раз
            ActionChains(self.driver).move_to_element(body).perform()
            time.sleep(2)  # Задержка между прокрутками

    def fetch_data(self, pages: int = 3) -> list:
        results = []
        for page in range(1, pages + 1):
            url = self.BASE_URL.format(page)
            logging.info("Fetching page %d: %s", page, url)
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div[3]/section/div[2]')))
            
            # Прокручиваем страницу, чтобы подгрузить все игры
            self.scroll_page()

            for i in range(1, 100):  # Пробуем парсить до 100 игр на странице
                try:
                    title_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a/div[3]/div/div[1]/h2'
                    price_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a/div[3]/div/div[3]/div/div/span'
                    url_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a'

                    title_elements = self.driver.find_elements(By.XPATH, title_xpath)
                    price_elements = self.driver.find_elements(By.XPATH, price_xpath)
                    url_elements = self.driver.find_elements(By.XPATH, url_xpath)

                    logging.info(f"Title elements found: {len(title_elements)}")
                    logging.info(f"Price elements found: {len(price_elements)}")

                    if title_elements:
                        title = title_elements[0].text.strip()

                        if price_elements:
                            # Извлекаем текст цены
                            price_text = price_elements[0].text.strip()
                            price_match = re.search(r"\$([0-9,]+\.[0-9]{2})", price_text)
                            if price_match:
                                price = float(price_match.group(1).replace(",", ""))  # Преобразуем строку в число
                            else:
                                price = 0.0
                        else:
                            price = 0.0

                        # Добавляем данные в список
                        results.append({"title": title, "price": price, "url": self.driver.current_url})
                        logging.info("Parsed game: %s | Price: %s", title, price)
                    else:
                        logging.warning("No title found for product %d on page %d", i, page)
                except Exception as ex:
                    logging.error(f"Error parsing game {i} on page {page}: {ex}")

        logging.info("Parsed %d games.", len(results))
        return results

    def save_to_json(self, data: list, filename: str = "nintendo_games.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info("Data saved to JSON file: %s", filename)

    def save_to_csv(self, data: list, filename: str = "nintendo_games.csv"):
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Название", "Цена", "URL"])
            for item in data:
                writer.writerow([item["title"], item["price"], item["url"]])
        logging.info("Data saved to CSV file: %s", filename)

    def close(self):
        self.driver.quit()
        logging.info("Selenium WebDriver closed.")


async def get_or_create_nintendo_store(session: AsyncSession) -> Store:
    result = await session.execute(select(Store).where(Store.name == "Nintendo Store"))
    store = result.scalars().first()
    if not store:
        store = Store(name="Nintendo Store", url="https://www.nintendo.com/us/store/games/best-sellers/")
        session.add(store)
        await session.commit()
        await session.refresh(store)
        logging.info("Store 'Nintendo Store' created in DB.")
    else:
        logging.info("Store 'Nintendo Store' already exists in DB.")
    return store


async def save_to_db(data: list):
    async with SessionLocal() as session:
        store = await get_or_create_nintendo_store(session)
        new_count = 0
        updated_count = 0
        logging.info("Processing data: ", data)

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
    parser = NintendoParser(headless=True)
    logging.info("Starting Nintendo parser...")
    data = parser.fetch_data(pages=3)
    if data:
        # parser.save_to_json(data)
        # parser.save_to_csv(data)
        await save_to_db(data)
    else:
        logging.warning("No data parsed from Nintendo Store.")
    parser.close()
