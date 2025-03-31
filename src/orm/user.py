from psycopg2 import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.users import User
from src.service.hashing import Hasher


async def get_user_by_username(username: str, async_db: AsyncSession):
    """
    Получить пользователя по имени.
    """
    query = select(User).where(User.username == username)
    result = await async_db.execute(query)
    return result.scalar_one_or_none()


async def create_user(user_data: dict, async_db: AsyncSession):
    """
    Создать нового пользователя.
    Принимает словарь user_data, в котором есть ключ 'password'.
    Этот ключ удаляется, и значение хешируется в 'hashed_password'.
    """
    user_data["hashed_password"] = Hasher.get_password_hash(user_data.pop("password"))
    user = User(**user_data)
    async_db.add(user)

    try:
        await async_db.commit()
        await async_db.refresh(user)
    except IntegrityError:
        await async_db.rollback()
        raise ValueError("Ошибка при создании пользователя.")

    return user


async def list_users(async_db: AsyncSession):
    """
    Получить список всех пользователей.
    """
    query = select(User)
    result = await async_db.execute(query)
    return result.scalars().all()


async def retrieve_user(user_id: int, async_db: AsyncSession):
    """
    Получить пользователя по его ID.
    """
    query = select(User).where(User.id == user_id)
    result = await async_db.execute(query)
    return result.scalar_one_or_none()
