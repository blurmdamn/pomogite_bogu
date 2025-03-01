from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session
from src.schemas.user import UserCreate, ShowUser
from src.orm import user as user_orm
from src.service.auth import get_current_user

api_router = APIRouter(prefix="/api/users", tags=["users"])


@api_router.post(
    "/create/",
    response_model=ShowUser,
    status_code=status.HTTP_201_CREATED,
    description="Создание нового пользователя",
)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_session)):
    return await user_orm.create_user(user_data=user.dict(), async_db=db)



@api_router.get(
    "/list/",
    response_model=List[ShowUser],
    status_code=status.HTTP_200_OK,
    description="Получение списка пользователей",
)
async def list_users(db: AsyncSession = Depends(get_async_session)):
    return await user_orm.list_users(async_db=db)


@api_router.get(
    "/detail/{user_id}/",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    description="Получение информации о пользователе",
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
    return await user_orm.retrieve_user(user_id=user_id, async_db=db)
