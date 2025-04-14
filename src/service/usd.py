import requests
from bs4 import BeautifulSoup

def get_usd_to_kzt() -> float:
    url = "https://www.x-rates.com/calculator/?from=USD&to=KZT&amount=1"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        result_div = soup.find("span", class_="ccOutputTrail").previous_sibling
        rate = float(result_div.text.strip().replace(",", ""))
        print(f"💱 Курс USD → KZT: {rate}")
        return rate
    except Exception as e:
        print(f"⚠️ Ошибка при получении курса: {e}")
        return 450.0  # fallback

# Пример использования
usd_to_kzt = get_usd_to_kzt()
