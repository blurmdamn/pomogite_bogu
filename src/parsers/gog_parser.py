from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import csv
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class GOGParser:
    def __init__(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")  # Запуск без открытия браузера
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("Browser initialized.")

    def fetch_gog_data(self, pages=3):
        base_url = "https://www.gog.com/ru/games?page={}"
        data = []

        for page in range(1, pages + 1):
            try:
                url = base_url.format(page)
                self.driver.get(url)
                logging.info(f"Fetching page {page}: {url}")

                self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="Catalog"]')))

                for i in range(1, 51):
                    try:
                        title_xpath = f'//*[@id="Catalog"]/div/div[2]/paginated-products-grid/div/product-tile[{i}]/a/div[2]/div[1]/product-title/span'
                        price_xpath = f'//*[@id="Catalog"]/div/div[2]/paginated-products-grid/div/product-tile[{i}]/a/div[2]/div[2]/div/product-price/price-value/span'

                        title_element = self.driver.find_elements(By.XPATH, title_xpath)
                        price_element = self.driver.find_elements(By.XPATH, price_xpath)

                        if title_element:
                            title = title_element[0].text.strip()
                            price = price_element[0].text.strip() if price_element else "Н/Д"
                            if price.lower() == "бесплатно":
                                price = "Н/Д"
                            data.append({'title': title, 'price': price})
                        else:
                            logging.warning(f"Title not found for game {i} on page {page}")
                    except Exception as ex:
                        logging.error(f"Error while fetching data for game {i} on page {page}: {ex}")

            except Exception as ex:
                logging.error(f"Error on page {page}: {ex}")

        return data

    def save_to_json(self, data, filename="gog_games.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")

    def save_to_csv(self, data, filename="gog_games.csv"):
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
    parser = GOGParser()
    try:
        data = parser.fetch_gog_data()
        parser.save_to_json(data)  # Сохранение в JSON
        parser.save_to_csv(data)   # Сохранение в CSV
    except Exception as ex:
        logging.error(f"Error: {ex}")
    finally:
        parser.close()
