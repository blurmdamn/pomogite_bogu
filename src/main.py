from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.route_user import api_router as user_router
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import asyncpg

# Настройка подключения к БД (на данный момент не используется в парсерах, но оставлена для будущего расширения)
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

app = FastAPI(title="My App", version="1.0")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # адрес вашего фронтенда (Vite обычно работает на 5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты для работы с пользователями (регистрация, логин, получение данных)
app.include_router(user_router)

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running"}

@app.get("/parse/steam")
def parse_steam():
    """
    Запускает парсер Steam, получает данные и возвращает их в виде JSON.
    """
    from src.parsers.steam_parser import SteamParser
    parser = SteamParser()
    try:
        data = parser.fetch_steam_data()
        return {"data": data}
    except Exception as ex:
        return {"error": str(ex)}
    finally:
        parser.close()

@app.get("/parse/gog")
def parse_gog():
    """
    Запускает парсер GOG, получает данные и возвращает их в виде JSON.
    """
    from src.parsers.gog_parser import GOGParser
    parser = GOGParser()
    try:
        data = parser.fetch_gog_data()
        return {"data": data}
    except Exception as ex:
        return {"error": str(ex)}
    finally:
        parser.close()

@app.get("/parse/nintendo")
def parse_nintendo():
    """
    Запускает парсер Nintendo, получает данные и возвращает их в виде JSON.
    """
    from src.parsers.nintendo_parser import NintendoParser
    parser = NintendoParser()
    try:
        data = parser.fetch_nintendo_data()
        return {"data": data}
    except Exception as ex:
        return {"error": str(ex)}
    finally:
        parser.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
