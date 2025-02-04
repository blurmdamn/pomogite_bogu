import concurrent.futures
from steam_parser import SteamParser
from epic_parser import EpicParser
from plati_parser import PlatiParser

def fetch_prices(urls: dict):
    """
    Функция для получения цен с разных платформ параллельно.
    :param urls: Словарь с ключами "steam", "epic", "plati" и соответствующими URL.
    :return: Словарь с полученными ценами.
    """
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        parsers = {
            "steam": SteamParser(),
            "epic": EpicParser(),
            "plati": PlatiParser()
        }
        
        futures = {platform: executor.submit(parser.get_price, urls[platform]) 
                   for platform, parser in parsers.items() if platform in urls}
        
        for platform, future in futures.items():
            try:
                results[platform] = future.result()
            except Exception as e:
                results[platform] = f"Ошибка: {e}"
    
    return results
