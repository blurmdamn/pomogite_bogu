from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class SteamParser:
    def __init__(self):
        # Настройка для Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Запуск без открытия браузера
        self.driver = webdriver.Chrome(options=chrome_options)  # WebDriver Manager найдет драйвер автоматически

    def fetch_steam_data(self):
        self.driver.get('https://store.steampowered.com/?l=russian')
        self.driver.implicitly_wait(5)  # Ждем загрузки страницы

        # Пример парсинга
        games = self.driver.find_elements("css selector", ".search_result_row")
        data = []
        for game in games[:5]:  # Парсим первые 5 игр для примера
            title = game.find_element("css selector", ".title").text
            price = game.find_element("css selector", ".search_price").text.strip()
            data.append({'title': title, 'price': price})
        return data

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    parser = SteamParser()
    try:
        data = parser.fetch_steam_data()
        print(data)  # Выводим в консоль
    finally:
        parser.close()
