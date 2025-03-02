from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session
from src.schemas.user import UserCreate, ShowUser
from src.orm import user as user_orm
from src.service.auth import create_access_token, get_current_user
from src.models.user import User  # для аннотаций

api_router = APIRouter(prefix="/api/users", tags=["users"])

@api_router.post(
    "/create/",
    response_model=ShowUser,
    status_code=status.HTTP_201_CREATED,
    description="Создание нового пользователя",
)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_session)):
    existing_user = await user_orm.get_user_by_username(username=user.username, async_db=db)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    new_user = await user_orm.create_user(user_data=user.dict(), async_db=db)
    return new_user

@api_router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session)
):
    user = await user_orm.get_user_by_username(username=form_data.username, async_db=db)
    if not user or not user_orm.Hasher.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = await create_access_token(user)
    return {"access_token": access_token, "token_type": "bearer"}

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
    user = await user_orm.retrieve_user(user_id=user_id, async_db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@api_router.get(
    "/me",
    response_model=ShowUser,
    description="Получение информации о текущем аутентифицированном пользователе"
)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
