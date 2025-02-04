from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class SteamParser:
    def __init__(self):
        # Настройка для Selenium
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Запуск без открытия браузера
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        print("Browser initialized.")

    def fetch_steam_data(self):
        self.driver.get('https://store.steampowered.com/search/?filter=globaltopsellers')
        self.driver.implicitly_wait(5)  # Ждем загрузки страницы

        # Пример парсинга
        data = []
        for i in range(1, 51):  # Парсим первые 5 игр для примера
            try:
                title_xpath = f'//*[@id="search_resultsRows"]/a[{i}]/div[2]/div[1]/span'
                price_xpath = f'//*[@id="search_resultsRows"]/a[{i}]/div[2]/div[4]/div/div/div/div'

                # Получаем название игры
                title = self.driver.find_element(By.XPATH, title_xpath).text
                
                # Попытка получения цены
                try:
                    price = self.driver.find_element(By.XPATH, price_xpath).text.strip()
                    if price.lower() == 'free':
                        price = "N/D"
                except Exception:
                    price = "N/D"
                
                data.append({'title': title, 'price': price})
            except Exception as ex:
                print(f"Error while fetching data for game {i}: {ex}")
        
        return data

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    print("Starting parser...")
    parser = SteamParser()
    try:
        data = parser.fetch_steam_data()
        print("Fetched data:")
        print(data)  # Выводим в консоль
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        parser.close()
