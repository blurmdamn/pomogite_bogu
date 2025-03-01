import time
import random
import logging
import asyncio
import re
import json
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from src.config import prod_db_settings
from src.models.product import Product
from src.models.store import Store

# ✅ Настроим логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Настроим подключение к БД через SQLAlchemy
DATABASE_URL = prod_db_settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def clean_price(price_text: str) -> float:
    """
    Форматирует цену:
      - Удаляет все символы, кроме цифр, запятых и точек.
      - Убирает пробелы внутри числа.
      - Заменяет запятую на точку.
      - Если цена 'free' или 'бесплатно', возвращает 0.0.
    """
    if not price_text or price_text.lower() in ["free", "бесплатно"]:
        return 0.0
    try:
        cleaned_price = re.sub(r"[^\d,\.]", "", price_text)
        cleaned_price = cleaned_price.replace(" ", "")
        cleaned_price = cleaned_price.replace(",", ".")
        return float(cleaned_price)
    except ValueError:
        logging.warning(f"⚠️ Error converting price: '{price_text}'")
        return 0.0


class GOGParser:
    BASE_URL = "https://www.gog.com/ru/games?page={}"

    def __init__(self, headless=True):
        """Инициализация Selenium WebDriver для GOG."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")  # ✅ Запуск без GUI
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("✅ Browser initialized for GOG.")

    def fetch_gog_data(self, pages=3):
        """Парсинг данных с сайта GOG с заданным числом страниц."""
        data = []
        base_url = self.BASE_URL
        for page in range(1, pages + 1):
            try:
                url = base_url.format(page)
                self.driver.get(url)
                logging.info(f"Fetching page {page}: {url}")
                self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="Catalog"]')))

                # Получаем список продуктов на странице (предполагается, что их 50 на страницу)
                for i in range(1, 51):
                    try:
                        title_xpath = f'//*[@id="Catalog"]/div/div[2]/paginated-products-grid/div/product-tile[{i}]/a/div[2]/div[1]/product-title/span'
                        price_xpath = f'//*[@id="Catalog"]/div/div[2]/paginated-products-grid/div/product-tile[{i}]/a/div[2]/div[2]/div/product-price/price-value/span'
                        title_elements = self.driver.find_elements(By.XPATH, title_xpath)
                        price_elements = self.driver.find_elements(By.XPATH, price_xpath)
                        if title_elements:
                            title = title_elements[0].text.strip()
                            price_text = price_elements[0].text.strip() if price_elements else ""
                            price = clean_price(price_text)
                            # Если у GOG нет URL на отдельную страницу для игры, можно использовать текущий URL
                            data.append({"title": title, "price": price, "url": url})
                        else:
                            logging.warning(f"Title not found for game {i} on page {page}")
                    except Exception as ex:
                        logging.error(f"Error while fetching data for game {i} on page {page}: {ex}")
            except Exception as ex:
                logging.error(f"Error on page {page}: {ex}")
        return data

    def save_to_json(self, data, filename="gog_games.json"):
        """Сохранение данных в JSON."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"📁 Data saved to {filename}")

    def save_to_csv(self, data, filename="gog_games.csv"):
        """Сохранение данных в CSV."""
        import csv
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Название", "Цена"])
            for game in data:
                writer.writerow([game["title"], game["price"]])
        logging.info(f"📁 Data saved to {filename}")

    def close(self):
        """Закрытие браузера."""
        self.driver.quit()
        logging.info("✅ Browser closed for GOG.")


async def get_or_create_gog_store(session: AsyncSession):
    """Проверяет, есть ли магазин 'GOG' в таблице Store, если нет – создаёт его."""
    result = await session.execute(select(Store).where(Store.name == "GOG"))
    store = result.scalars().first()
    if not store:
        store = Store(name="GOG", url="https://www.gog.com/ru/games")
        session.add(store)
        await session.commit()
        await session.refresh(store)
        logging.info("✅ Store 'GOG' added to DB.")
    else:
        logging.info("✅ Store 'GOG' already exists.")
    return store


async def save_games_to_db(games):
    """Сохранение списка игр в PostgreSQL через SQLAlchemy."""
    async with SessionLocal() as session:
        gog_store = await get_or_create_gog_store(session)
        new_games_count = 0
        updated_games_count = 0

        for game in games:
            existing_game = await session.execute(
                select(Product).where(
                    Product.name == game["title"],
                    Product.store_id == gog_store.id
                )
            )
            existing_game = existing_game.scalars().first()

            if existing_game:
                # Если игра уже есть, обновляем цену и валюту
                existing_game.price = game["price"]
                existing_game.currency = "USD"  # ✅ Для GOG явно указываем валюту
                updated_games_count += 1
            else:
                # Если игры нет, создаем новую запись
                game_entry = Product(
                    name=game["title"],
                    price=game["price"],
                    currency="USD",  # ✅ Для GOG явно указываем валюту
                    url=game["url"],
                    store_id=gog_store.id
                )
                session.add(game_entry)
                new_games_count += 1

        await session.commit()
        logging.info(f"✅ {new_games_count} new games added to DB.")
        logging.info(f"✅ {updated_games_count} existing games updated in DB.")

async def main():
    """Основной метод для запуска парсера GOG и сохранения данных."""
    logging.info("🚀 Starting GOG parser...")
    parser = GOGParser(headless=True)
    try:
        data = parser.fetch_gog_data(pages=3)
        if data:
            parser.save_to_json(data)
            parser.save_to_csv(data)
            await save_games_to_db(data)
    except Exception as ex:
        logging.error(f"❌ Unexpected error: {ex}")
    finally:
        parser.close()


if __name__ == "__main__":
    asyncio.run(main())
