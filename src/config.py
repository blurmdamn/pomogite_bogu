import os
from dotenv import load_dotenv
load_dotenv()


# Settings of project information.
project_settings = {
    "title": "Fast API application",
    "version": "1.0",
    "description": "Fast API application. Application include asyncpg+sqlalchemy technologies",
}


# Settings for database connection
class ProdDBSettings:
    """
    Класс, содержащий основные настройки для подключения к рабочей базе данных.
    """
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT", 5432)
    DB_NAME: str = os.getenv("DB_NAME")
    DATABASE_URL: str = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
prod_db_settings = ProdDBSettings()


from pydantic import BaseModel

class JWTSettings(BaseModel):
    JWT_SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    TOKEN_LIFESPAN: int = 3600  # Время жизни токена в секундах (1 час)

jwt_token_settings = JWTSettings()
