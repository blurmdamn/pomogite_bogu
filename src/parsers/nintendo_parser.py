import time
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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ✅ Настроим подключение к БД через SQLAlchemy
DATABASE_URL = prod_db_settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def clean_price(price_text: str) -> float:
    """Форматирует цену: удаляет лишние символы и преобразует в число."""
    if not price_text or price_text.lower() in ["free", "бесплатно"]:
        return 0.0
    try:
        cleaned_price = re.sub(r"[^\d,\.]", "", price_text)
        cleaned_price = cleaned_price.replace(" ", "").replace(",", ".")
        return float(cleaned_price)
    except ValueError:
        logging.warning(f"⚠️ Ошибка преобразования цены: '{price_text}'")
        return 0.0


class NintendoParser:
    BASE_URL = "https://www.nintendo.com/us/store/games/best-sellers/#sort=df&p={}"

    def __init__(self, headless=True):
        """Инициализация Selenium WebDriver для Nintendo Store."""
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
        logging.info("✅ Браузер для Nintendo Store запущен.")

    def fetch_nintendo_data(self, pages=3):
        """Парсинг данных с сайта Nintendo Store с заданным числом страниц."""
        data = []
        for page in range(pages):
            try:
                url = self.BASE_URL.format(page)
                self.driver.get(url)
                logging.info(f"🔍 Обрабатываем страницу {page}: {url}")
                time.sleep(3)  # Даем время на загрузку

                for i in range(1, 100):  # Пробуем парсить 100 игр на странице
                    try:
                        title_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a/div[2]/div/div[1]/h2'
                        price_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a/div[2]/div/div[2]/div/div/span'
                        url_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a'

                        title_elements = self.driver.find_elements(By.XPATH, title_xpath)
                        price_elements = self.driver.find_elements(By.XPATH, price_xpath)
                        url_elements = self.driver.find_elements(By.XPATH, url_xpath)

                        if title_elements:
                            title = title_elements[0].text.strip()
                            price_text = price_elements[0].text.strip() if price_elements else ""
                            price = clean_price(price_text)
                            game_url = url_elements[0].get_attribute("href") if url_elements else url

                            data.append({"title": title, "price": price, "url": game_url})
                        else:
                            logging.warning(f"⚠️ Игра {i} не найдена на странице {page}")
                    except Exception as ex:
                        logging.error(f"❌ Ошибка при парсинге игры {i} на странице {page}: {ex}")

            except Exception as ex:
                logging.error(f"❌ Ошибка при загрузке страницы {page}: {ex}")
        return data

    def save_to_json(self, data, filename="nintendo_games.json"):
        """Сохранение данных в JSON."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"📁 Данные сохранены в {filename}")

    def save_to_csv(self, data, filename="nintendo_games.csv"):
        """Сохранение данных в CSV."""
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Название", "Цена", "Ссылка"])
            for game in data:
                writer.writerow([game["title"], game["price"], game["url"]])
        logging.info(f"📁 Данные сохранены в {filename}")

    def close(self):
        """Закрытие браузера."""
        self.driver.quit()
        logging.info("✅ Браузер для Nintendo Store закрыт.")


async def get_or_create_nintendo_store(session: AsyncSession):
    """Проверяет, есть ли магазин 'Nintendo Store' в таблице Store, если нет – создаёт его."""
    result = await session.execute(select(Store).where(Store.name == "Nintendo Store"))
    store = result.scalars().first()
    if not store:
        store = Store(name="Nintendo Store", url="https://www.nintendo.com/us/store/games/best-sellers/")
        session.add(store)
        await session.commit()
        await session.refresh(store)
        logging.info("✅ Магазин 'Nintendo Store' добавлен в БД.")
    else:
        logging.info("✅ Магазин 'Nintendo Store' уже есть в БД.")
    return store


async def save_games_to_db(games):
    """Сохранение списка игр в PostgreSQL через SQLAlchemy."""
    async with SessionLocal() as session:
        nintendo_store = await get_or_create_nintendo_store(session)
        new_games_count = 0
        updated_games_count = 0

        for game in games:
            existing_game = await session.execute(
                select(Product).where(
                    Product.name == game["title"],
                    Product.store_id == nintendo_store.id
                )
            )
            existing_game = existing_game.scalars().first()

            if existing_game:
                existing_game.price = game["price"]
                existing_game.currency = "USD"
                updated_games_count += 1
            else:
                game_entry = Product(
                    name=game["title"],
                    price=game["price"],
                    currency="USD",
                    url=game["url"],
                    store_id=nintendo_store.id
                )
                session.add(game_entry)
                new_games_count += 1

        await session.commit()
        logging.info(f"✅ {new_games_count} новых игр добавлено в БД.")
        logging.info(f"✅ {updated_games_count} обновлено существующих игр.")


async def main():
    """Основной метод для запуска парсера Nintendo и сохранения данных."""
    logging.info("🚀 Запуск парсера Nintendo Store...")
    parser = NintendoParser(headless=True)
    try:
        data = parser.fetch_nintendo_data(pages=3)
        if data:
            parser.save_to_json(data)
            parser.save_to_csv(data)
            await save_games_to_db(data)
    except Exception as ex:
        logging.error(f"❌ Ошибка: {ex}")
    finally:
        parser.close()


if __name__ == "__main__":
    asyncio.run(main())
