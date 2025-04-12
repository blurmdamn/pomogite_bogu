from fastapi import APIRouter, Depends, status
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
    "/search",
    response_model=List[ShowProductWithStore],  # 👈 тут заменили ShowProduct
    status_code=status.HTTP_200_OK,
    description="Для отображения в поиске",
)
async def search_products_route(
    q: str, db: AsyncSession = Depends(get_async_session)
):
    return await product_orm.search_products(query=q, async_db=db)


@api_router.get(
    "/detail/{product_id}/",
    response_model=ShowProduct,
    status_code=status.HTTP_200_OK,
    description="Получение информации о продукте",
)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_session)):
    return await product_orm.retrieve_product(product_id=product_id, async_db=db)

from fastapi import Query

@api_router.get(
    "/search/",
    response_model=List[ProductSearchResult],
    status_code=status.HTTP_200_OK,
    description="Поиск игр по названию"
)
async def search_products(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_async_session)
):
    return await product_orm.search_products(query=q, async_db=db)
