import time
import json
import csv
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Настроим логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("nintendo_parser.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class NintendoParser:
    def __init__(self):
        logging.info("Initializing browser...")
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Запуск без GUI
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        logging.info("Browser initialized.")

    def fetch_nintendo_data(self):
        url = "https://www.nintendo.com/us/store/games/best-sellers/#sort=df&p=0"
        data = []

        logging.info("Starting data fetch...")
        self.driver.get(url)
        time.sleep(3)  # Даем время странице загрузиться
        logging.info("Processing page 0...")

        for i in range(1, 100):  # Пробуем парсить 100 элементов
            try:
                title_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a/div[2]/div/div[1]/h2'
                price_xpath = f'//*[@id="main"]/div[3]/section/div[2]/div[2]/div[{i}]/div/a/div[2]/div/div[2]/div/div/span'

                title = self.driver.find_element(By.XPATH, title_xpath).text.strip()

                try:
                    price = self.driver.find_element(By.XPATH, price_xpath).text.strip()
                    if not price or price.lower() == "free":
                        price = "Н/Д"
                except Exception:
                    price = "Н/Д"

                game_info = {"title": title, "price": price}
                data.append(game_info)
            except Exception:
                logging.info("No more games found. Stopping parsing.")
                break  # Если элемент отсутствует, останавливаем парсинг

        logging.info(f"Fetched {len(data)} games in total.")
        return data

    def save_to_json(self, data, filename="nintendo_games.json"):
        """Сохранение данных в JSON."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")

    def save_to_csv(self, data, filename="nintendo_games.csv"):
        """Сохранение данных в CSV."""
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Название", "Цена"])
            for game in data:
                writer.writerow([game["title"], game["price"]])
        logging.info(f"Data saved to {filename}")

    def close(self):
        self.driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    logging.info("Starting Nintendo Store parser...")
    parser = NintendoParser()
    try:
        data = parser.fetch_nintendo_data()
        if data:
            parser.save_to_json(data)  # Сохранение в JSON
            parser.save_to_csv(data)   # Сохранение в CSV
    except Exception as ex:
        logging.error(f"Unexpected error: {ex}", exc_info=True)
    finally:
        parser.close()
