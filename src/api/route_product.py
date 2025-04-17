from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session
from src.schemas.product import ProductCreate, ProductSearchResult, ShowProduct, ShowProductWithStore
from src.orm import product as product_orm
from src.service.auth import get_current_user

api_router = APIRouter(prefix="/api/products", tags=["products"])


@api_router.post(
    "/create/",
    response_model=ShowProduct,
    status_code=status.HTTP_201_CREATED,
    description="Добавление нового продукта в список желаемого",
)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    return await product_orm.create_new_product(
        product_schema=product, async_db=db, user_id=current_user.id
    )


@api_router.get(
    "/search/",
    response_model=List[ShowProductWithStore],
    status_code=status.HTTP_200_OK,
    description="Комбинированный поиск по названию с использованием FTS и ILIKE",
)
async def search_products(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Использует:
    - TS-вектор для Steam (russian) и GOG (english)
    - ILIKE для магазинов без описаний/векторов (например, Nintendo)
    """
    return await product_orm.search_products(query=q, async_db=db)


@api_router.get(
    "/detail/{product_id}/",
    response_model=ShowProduct,
    status_code=status.HTTP_200_OK,
    description="Получение информации о продукте",
)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    return await product_orm.retrieve_product(product_id=product_id, async_db=db)


@api_router.get(
    "/smart_search",
    response_model=List[ShowProductWithStore],
    status_code=status.HTTP_200_OK,
    description="Умный полнотекстовый поиск по описанию с сортировкой по релевантности"
)
async def smart_search_products_route(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_async_session)
):
    return await product_orm.smart_search_products(query=q, async_db=db)


@api_router.get(
    "/list",
    response_model=List[ShowProductWithStore],
    status_code=status.HTTP_200_OK,
    description="Список всех продуктов (для отображения на главной)"
)
async def list_all_products(db: AsyncSession = Depends(get_async_session)):
    return await product_orm.get_all_products(async_db=db)


@api_router.get(
    "/by_store/{store_name}",
    response_model=List[ShowProductWithStore],
    status_code=status.HTTP_200_OK,
    description="Получить продукты по магазину"
)
async def get_products_by_store(
    store_name: str,
    db: AsyncSession = Depends(get_async_session)
):
    return await product_orm.get_products_by_store(store_name=store_name, async_db=db)
