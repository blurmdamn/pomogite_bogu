from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.config import jwt_token_settings
from src.database import get_async_session
from src.models.users import User
from src.orm.user import get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token/")

async def create_access_token(user: User):
    """
    Функция создания JWT токена.
    В функцию передаются данные пользователя, которые включаются в полезную нагрузку токена.
    Время жизни токена устанавливается с помощью 'expires_delta'.
    """
    expire = datetime.utcnow() + timedelta(seconds=jwt_token_settings.TOKEN_LIFESPAN)
    payload = {
        "sub": user.username,
        "email": user.email,
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        jwt_token_settings.JWT_SECRET_KEY,
        algorithm=jwt_token_settings.ALGORITHM,
    )
    return token

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_async_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token,
            jwt_token_settings.JWT_SECRET_KEY,
            algorithms=[jwt_token_settings.ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Передаем параметр как async_db=db, так как функция ожидает именно это имя
    user = await get_user_by_username(username=username, async_db=db)
    if user is None:
        raise credentials_exception
    return user
