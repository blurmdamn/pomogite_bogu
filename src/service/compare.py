from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.products import Product
from src.models.wishlists import Wishlist
from src.models.users import User
from src.models.wishlists_products import wishlist_product
from src.schemas.notification import NotificationCreate
from src.service.notification import send_notification

USD_TO_KZT = 450  # Примерный курс доллара к тенге

def normalize_price(price: float, store_name: str) -> float:
    if store_name.lower() == "steam":
        return price
    elif store_name.lower() in ["gog", "nintendo"]:
        return price * USD_TO_KZT
    else:
        return price

async def find_and_notify_cheaper_games(db: AsyncSession):
    result = await db.execute(select(Product))
    all_products = result.scalars().all()

    grouped_by_name = defaultdict(list)
    for product in all_products:
        if product.price:
            grouped_by_name[product.name.lower()].append(product)

    for name, games in grouped_by_name.items():
        if len(games) < 2:
            continue

        sorted_games = sorted(games, key=lambda g: normalize_price(g.price, g.store.name))
        cheapest = sorted_games[0]

        for game in sorted_games[1:]:
            price_a = normalize_price(cheapest.price, cheapest.store.name)
            price_b = normalize_price(game.price, game.store.name)

            print(f"\n🔎 Сравнение: {cheapest.name}")
            print(f"  ✅ {cheapest.store.name}: {cheapest.price} → {price_a}")
            print(f"  ⚠️  {game.store.name}: {game.price} → {price_b}")

            # Уведомляем всегда при наличии сравнения
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
