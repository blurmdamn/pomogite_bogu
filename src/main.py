from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import asyncpg

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

app = FastAPI()

class SteamParseRequest(BaseModel):
    param: str

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running"}

@app.get("/parse/steam")
def parse_steam():
    return {"message": "Steam parser will be implemented here"}

@app.get("/parse/epic")
def parse_epic():
    return {"message": "Epic parser will be implemented here"}

@app.get("/parse/plati")
def parse_plati():
    return {"message": "Plati parser will be implemented here"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
