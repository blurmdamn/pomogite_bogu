import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.products import Product
from src.models.wishlists import Wishlist
from src.models.users import User
from src.models.wishlists_products import wishlist_product
from src.schemas.notification import NotificationCreate
from src.service.notification import send_notification


# Получение курса доллара к тенге через парсинг сайта
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

def normalize_price(price: float, store_name: str, usd_to_kzt: float) -> float:
    if store_name.lower() == "steam":
        return price
    elif store_name.lower() in ["gog", "nintendo"]:
        return price * usd_to_kzt
    else:
        return price

async def find_and_notify_cheaper_games(db: AsyncSession):
    usd_to_kzt = get_usd_to_kzt()
    print(f"💱 Курс USD→KZT: {usd_to_kzt:.2f}")

    result = await db.execute(select(Product))
    all_products = result.scalars().all()

    grouped_by_name = defaultdict(list)
    for product in all_products:
        if product.price:
            grouped_by_name[product.name.lower()].append(product)

    for name, games in grouped_by_name.items():
        if len(games) < 2:
            continue

        sorted_games = sorted(games, key=lambda g: normalize_price(g.price, g.store.name, usd_to_kzt))
        cheapest = sorted_games[0]

        for game in sorted_games[1:]:
            price_a = normalize_price(cheapest.price, cheapest.store.name, usd_to_kzt)
            price_b = normalize_price(game.price, game.store.name, usd_to_kzt)

            print(f"\n🔎 Сравнение: {cheapest.name}")
            print(f"  ✅ {cheapest.store.name}: {cheapest.price} → {price_a}")
            print(f"  ⚠️  {game.store.name}: {game.price} → {price_b}")

            wish_query = await db.execute(
                select(Wishlist)
                .join(wishlist_product, Wishlist.id == wishlist_product.c.wishlist_id)
                .where(wishlist_product.c.product_id == cheapest.id)
            )
            wishlists = wish_query.scalars().all()

            for wishlist in wishlists:
                user_query = await db.execute(
                    select(User).where(User.id == wishlist.user_id)
                )
                user = user_query.scalar_one_or_none()
                if user:
                    message = (
                        f"🎮 {cheapest.name} сейчас дешевле в {cheapest.store.name} — {cheapest.price}₸/$!\n"
                        f"В {game.store.name} стоит {game.price}₸/$.\n"
                        f"Ссылка: {cheapest.url}"
                    )
                    notification_data = NotificationCreate(
                        message=message,
                        user_id=user.id,
                        product_id=cheapest.id,
                    )
                    await send_notification(notification_data, db)
                    print(f"✅ Уведомление создано для пользователя ID {user.id}")
