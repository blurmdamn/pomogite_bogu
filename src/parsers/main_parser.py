import concurrent.futures
from steam_parser import SteamParser
from gog_parser import GOGParser
from nintendo_parser import NintendoParser

def fetch_prices(urls: dict):
    """
    Функция для получения цен с разных платформ параллельно.
    :param urls: Словарь с ключами "steam", "gog", "nintendo" и соответствующими URL.
    :return: Словарь с полученными ценами.
    """
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        parsers = {
            "steam": SteamParser(),
            "gog": GOGParser(),
            "nintendo": NintendoParser()
        }
        
        futures = {platform: executor.submit(parser.get_price, urls[platform]) 
                   for platform, parser in parsers.items() if platform in urls}
        
        for platform, future in futures.items():
            try:
                results[platform] = future.result()
            except Exception as e:
                results[platform] = f"Ошибка: {e}"
    
    return results
