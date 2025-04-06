from fastapi import APIRouter
from src.parsers.steam_parser import main as parse_steam
from src.parsers.gog_parser import main as parse_gog
from src.parsers.nintendo_parser import main as parse_nintendo

api_router = APIRouter(prefix="/parse", tags=["parsers"])


@api_router.get("/steam")
async def run_steam_parser():
    await parse_steam()
    return {"status": "Steam parsed successfully"}


@api_router.get("/gog")
async def run_gog_parser():
    await parse_gog()
    return {"status": "GOG parsed successfully"}


@api_router.get("/nintendo")
async def run_nintendo_parser():
    await parse_nintendo()
    return {"status": "Nintendo parsed successfully"}
