from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import asyncpg

# Настройка подключения к БД (на данный момент не используется в парсерах, но оставлена для будущего расширения)
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

app = FastAPI()


# Пример модели запроса (если потребуется передавать какие-либо параметры в будущем)
class SteamParseRequest(BaseModel):
    param: str


@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running"}


@app.get("/parse/steam")
def parse_steam():
    """
    Запускает парсер Steam, получает данные и возвращает их в виде JSON.
    """
    # Импортируем парсер из пакета src.parsers
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
