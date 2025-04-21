from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session
from src.schemas.wishlist import WishlistAddProduct, WishlistCreate, ShowWishlist
from src.orm import wishlist as wishlist_orm
from src.service.auth import get_current_user

api_router = APIRouter(prefix="/api/wishlists", tags=["wishlists"])


@api_router.post(
    "/create/",
    response_model=ShowWishlist,
    status_code=status.HTTP_201_CREATED,
    description="Создание нового списка желаемого",
)
async def create_wishlist(
    wishlist: WishlistCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    return await wishlist_orm.create_new_wishlist(
        wishlist_schema=wishlist, async_db=db, user_id=current_user.id
    )


@api_router.get(
    "/list/",
    response_model=List[ShowWishlist],
    status_code=status.HTTP_200_OK,
    description="Получение списка желаемого текущего пользователя",
)
async def list_user_wishlists(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    return await wishlist_orm.list_wishlists_by_user(user_id=current_user.id, async_db=db)


@api_router.get(
    "/detail/{wishlist_id}/",
    response_model=ShowWishlist,
    status_code=status.HTTP_200_OK,
    description="Получение информации о списке желаемого",
)
async def get_wishlist(wishlist_id: int, db: AsyncSession = Depends(get_async_session)):
    return await wishlist_orm.retrieve_wishlist(wishlist_id=wishlist_id, async_db=db)


@api_router.post(
    "/add",
    status_code=status.HTTP_200_OK,
    description="Добавить продукт в вишлист текущего пользователя"
)
async def add_product_to_wishlist(
    payload: WishlistAddProduct,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user)
):
    return await wishlist_orm.add_product_to_user_wishlist(
        user_id=current_user.id,
        product_id=payload.product_id,
        async_db=db
    )


@api_router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Удалить продукт из вишлиста текущего пользователя"
)
async def remove_product_from_wishlist(
    product_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user)
):
    await wishlist_orm.remove_product_from_user_wishlist(
        user_id=current_user.id,
        product_id=product_id,
        async_db=db
    )
