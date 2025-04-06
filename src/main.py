from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from src.api.route_user import api_router as user_router
from src.api.router import api_router  # 👈 общий роутер с включёнными маршрутами
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import asyncpg

# Настройка подключения к БД
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
# app.include_router(user_router)
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running"}

# @app.get("/parse/steam")
# async def parse_steam():
#     """
#     Запускает парсер Steam, получает данные и возвращает их в виде JSON.
#     """
#     from src.parsers.steam_parser import SteamParser,main
#     parser = SteamParser()
#     await main()
#     return {"status": "Steam parsed successfully"}
   
# @app.get("/parse/gog")
# async def parse_gog():
#     """
#     Запускает парсер GOG, получает данные и возвращает их в виде JSON.
#     """
#     from src.parsers.gog_parser import GOGParser, main
#     parser = GOGParser()
#     await main()
#     return {"data": "data"}
    

# @app.get("/parse/nintendo")
# async def parse_nintendo():
#     from src.parsers.nintendo_parser import main
#     await main()
#     return {"status": "Nintendo parsed successfully"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
