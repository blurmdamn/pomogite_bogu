from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session
from src.schemas.product import ShowProduct
from src.orm import product as product_orm

api_router = APIRouter(prefix="/api/games", tags=["search"])


@api_router.get("/search", response_model=List[ShowProduct])
async def search_games(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_async_session)
):
    return await product_orm.search_games_by_title(q, db)
