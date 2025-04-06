from fastapi import APIRouter

from src.api.route_user import api_router as user_router
from src.api.route_wishlist import api_router as wishlist_router
from src.api.route_store import api_router as store_router
from src.api.route_product import api_router as product_router
from src.api.route_notification import api_router as notification_router
from src.api.route_parsers import api_router as parser_router  # 👈 добавим парсеры сюда

api_router = APIRouter()

# 👇 Подключаем все маршруты
api_router.include_router(user_router)
api_router.include_router(wishlist_router)
api_router.include_router(store_router)
api_router.include_router(product_router)
api_router.include_router(notification_router)
api_router.include_router(parser_router)  # 👈 парсеры
