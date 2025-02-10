import time
import random
import logging
import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Настроим логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SteamParser:
    def __init__(self, headless=True):
        chrome_options = Options()
            #chrome_options.add_argument("--headless")  # Запуск без GUI
        chrome_options.add_argument("--disable-dev-shm-usage")  # Исправление для Docker/Linux
        chrome_options.add_argument("--no-sandbox")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        logging.info("Browser initialized.")

    def scroll_down(self):
        """Прокручивает страницу вниз для загрузки новых элементов."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))  # Динамическая задержка для естественности
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Выходим, если больше нет изменений
            last_height = new_height
        logging.info("Scrolling completed.")

    def fetch_steam_data(self):
        try:
            self.driver.get("https://store.steampowered.com/search/?filter=globaltopsellers")
            self.driver.implicitly_wait(5)
            
            # Ждём появления первой игры
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="search_resultsRows"]/a[1]')))
            
            self.scroll_down()  # Прокручиваем страницу вниз перед парсингом
            
            data = []
            game_elements = self.driver.find_elements(By.XPATH, '//*[@id="search_resultsRows"]/a')
            logging.info(f"Found {len(game_elements)} games.")

            for index, game in enumerate(game_elements, start=1):
                try:
                    title = game.find_element(By.XPATH, './/div[2]/div[1]/span').text
                    try:
                        price = game.find_element(By.XPATH, './/div[2]/div[4]/div/div/div/div').text.strip()
                        if price.lower() == "free":
                            price = "N/D"
                    except NoSuchElementException:
                        price = "N/D"
                    data.append({"title": title, "price": price})
                except Exception as ex:
                    logging.warning(f"Error while fetching data for game {index}: {ex}")

            return data
        except TimeoutException:
            logging.error("Page load timed out. No data retrieved.")
            return []

    def save_to_json(self, data, filename="steam_games.json"):
        """Сохранение данных в JSON."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")

    def save_to_csv(self, data, filename="steam_games.csv"):
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
    logging.info("Starting parser...")
    parser = SteamParser()
    try:
        data = parser.fetch_steam_data()
        if data:
            parser.save_to_json(data)  # Сохранение в JSON
            parser.save_to_csv(data)   # Сохранение в CSV
    except Exception as ex:
        logging.error(f"Unexpected error: {ex}")
    finally:
        parser.close()

