from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session
from src.schemas.store import StoreCreate, ShowStore
from src.orm import store as store_orm

api_router = APIRouter(prefix="/api/stores", tags=["stores"])


@api_router.post(
    "/create/",
    response_model=ShowStore,
    status_code=status.HTTP_201_CREATED,
    description="Создание нового магазина",
)
async def create_store(store: StoreCreate, db: AsyncSession = Depends(get_async_session)):
    return await store_orm.create_new_store(store_schema=store, async_db=db)


@api_router.get(
    "/list/",
    response_model=List[ShowStore],
    status_code=status.HTTP_200_OK,
    description="Получение списка магазинов",
)
async def list_stores(db: AsyncSession = Depends(get_async_session)):
    return await store_orm.list_stores(async_db=db)
