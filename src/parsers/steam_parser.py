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

from src.config import prod_db_settings
from src.models.products import Product
from src.models.stores import Store

# ✅ Настроим логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Настроим подключение к БД через SQLAlchemy
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
                break  # Выходим, если больше нет изменений
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
            cleaned_price = cleaned_price.replace(" ", "")
            cleaned_price = cleaned_price.replace(",", ".")
            return float(cleaned_price)
        except ValueError:
            logging.warning(f"⚠️ Error converting price: '{price_text}'")
            return 0.0

    def fetch_steam_data(self):
        """Парсинг данных с сайта Steam."""
        try:
            self.driver.get(self.BASE_URL)
            self.driver.implicitly_wait(10)

            # Ждем появления первой игры
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="search_resultsRows"]/a[1]')))

            self.scroll_down()

            data = []
            game_elements = self.driver.find_elements(By.XPATH, '//*[@id="search_resultsRows"]/a')
            logging.info(f"🎮 Found {len(game_elements)} games.")

            for index, game in enumerate(game_elements, start=1):
                try:
                    title = game.find_element(By.XPATH, './/div[2]/div[1]/span').text
                    url = game.get_attribute("href")
                    try:
                        price_text = game.find_element(By.XPATH, './/div[2]/div[4]/div/div/div/div').text.strip()
                    except NoSuchElementException:
                        price_text = ""
                    price = self.clean_price(price_text)
                    data.append({"title": title, "price": price, "url": url})
                except Exception as ex:
                    logging.warning(f"⚠️ Error while fetching data for game {index}: {ex}")

            return data
        except TimeoutException:
            logging.error("❌ Page load timed out. No data retrieved.")
            return []

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


async def save_games_to_db(games):
    """Сохранение списка игр в PostgreSQL через SQLAlchemy."""
    async with SessionLocal() as session:
        steam_store = await get_or_create_steam_store(session)
        new_games_count = 0
        updated_games_count = 0

        for game in games:
            existing_game = await session.execute(
                select(Product).where(
                    Product.name == game["title"],
                    Product.store_id == steam_store.id
                )
            )
            existing_game = existing_game.scalars().first()

            if existing_game:
                # Если игра уже есть, обновляем цену и валюту
                existing_game.price = game["price"]
                existing_game.currency = "KZT"  # ✅ Для Steam явно указываем валюту
                updated_games_count += 1
            else:
                # Если игры нет, создаем новую запись
                game_entry = Product(
                    name=game["title"],
                    price=game["price"],
                    currency="KZT",  # ✅ Для Steam явно указываем валюту
                    url=game["url"],
                    store_id=steam_store.id  # Связываем игру с магазином
                )
                session.add(game_entry)
                new_games_count += 1

        await session.commit()
        logging.info(f"✅ {new_games_count} new games added to DB.")
        logging.info(f"✅ {updated_games_count} existing games updated in DB.")


async def main():
    """Основной метод для запуска парсера и сохранения данных."""
    logging.info("🚀 Starting parser...")
    parser = SteamParser(headless=True)
    try:
        data = parser.fetch_steam_data()
        if data:
            await save_games_to_db(data)
    except Exception as ex:
        logging.error(f"❌ Unexpected error: {ex}")
    finally:
        parser.close()


if __name__ == "__main__":
    asyncio.run(main())
