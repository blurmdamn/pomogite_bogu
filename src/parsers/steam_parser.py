import time
import random
import logging
import asyncio
import re

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
from sqlalchemy.sql.expression import and_

from src.config import prod_db_settings
from src.models.products import Product
from src.models.stores import Store

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Настройка подключения к БД через SQLAlchemy
DATABASE_URL = prod_db_settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class SteamParser:
    BASE_URL = "https://store.steampowered.com/search/?filter=globaltopsellers"

    def __init__(self, headless=True):
        """Инициализация Selenium WebDriver."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")  # ✅ Запуск без GUI
        chrome_options.add_argument("--disable-dev-shm-usage")  # Исправление для Docker/Linux
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        logging.info("✅ Browser initialized.")

    def scroll_down(self):
        """Прокручивает страницу вниз для загрузки новых элементов."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))  # Динамическая задержка
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Выходим, если изменений нет
            last_height = new_height
        logging.info("✅ Scrolling completed.")

    @staticmethod
    def clean_price(price_text):
        """
        Форматирует цену:
         - Убирает все символы, кроме цифр, запятых и точек,
         - Удаляет пробелы внутри числа,
         - Заменяет запятую на точку,
         - Если цена 'free' или 'бесплатно', возвращает 0.0.
        """
        if not price_text or price_text.lower() in ["free", "бесплатно"]:
            return 0.0
        try:
            cleaned_price = re.sub(r"[^\d,\.]", "", price_text)
            cleaned_price = cleaned_price.replace(" ", "").replace(",", ".")
            return float(cleaned_price)
        except ValueError:
            logging.warning(f"⚠️ Error converting price: '{price_text}'")
            return 0.0

    def fetch_steam_data(self):
        """Парсинг данных с сайта Steam."""
        logging.info("🚀 Opening Steam store page...")
        self.driver.get(self.BASE_URL)
        self.driver.implicitly_wait(10)

        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="search_resultsRows"]/a[1]')))

        self.scroll_down()

        data = []
        game_elements = self.driver.find_elements(By.XPATH, '//*[@id="search_resultsRows"]/a')
        logging.info(f"🎮 Found {len(game_elements)} games.")

        for index, game in enumerate(game_elements, start=1):
            time.sleep(3)
            try:
                title = game.find_element(By.XPATH, './/div[2]/div[1]/span').text
            except NoSuchElementException:
                logging.warning(f"⚠️ No title found for game at index {index}. Skipping.")
                continue  # Если нет названия, пропускаем игру

            url = game.get_attribute("href")
            try:
                price_text = game.find_element(By.XPATH, './/div[2]/div[4]/div/div/div/div').text.strip()
            except NoSuchElementException:
                logging.warning(f"⚠️ No price found for '{title}', skipping this game.")
                continue  # Если цена отсутствует, пропускаем игру
            # Если блок цены отсутствует, пропускаем игру
            price = self.clean_price(price_text) if price_text else None
            if price is None:
                continue  # Пропускаем игры без цены

            data.append({"title": title, "price": price, "url": url})
        logging.info("Parsed data: %s", data)
        return data

    def close(self):
        """Закрытие браузера."""
        self.driver.quit()
        logging.info("✅ Browser closed.")


async def get_or_create_steam_store(session: AsyncSession):
    """
    Проверяет, есть ли магазин 'Steam' в таблице Store, если нет – создает его.
    """
    result = await session.execute(select(Store).where(Store.name == "Steam"))
    store = result.scalars().first()
    if not store:
        store = Store(name="Steam", url="https://store.steampowered.com/")
        session.add(store)
        await session.commit()
        await session.refresh(store)
        logging.info("✅ Store 'Steam' added to DB.")
    else:
        logging.info("✅ Store 'Steam' already exists.")
    return store


async def save_to_db(data: list):
    """Сохранение списка игр в PostgreSQL через SQLAlchemy."""
    async with SessionLocal() as session:
        store = await get_or_create_steam_store(session)
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
    """Основной метод для запуска парсера и сохранения данных."""
    logging.info("🚀 Starting parser...")
    parser = SteamParser(headless=True)
    data = parser.fetch_steam_data()
    print("✅ Parsed data:", data)
    if data:
        await save_to_db(data)
    else:
        logging.warning("No data parsed from Steam Store.")
    parser.close()

