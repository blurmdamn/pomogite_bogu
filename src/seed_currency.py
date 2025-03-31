from sqlalchemy import text
import asyncio
from src.database import async_session_maker

async def seed_currency():
    async with async_session_maker() as session:
        # Используем ON CONFLICT DO NOTHING, чтобы не пытаться вставить валюту, если она уже есть.
        query = text("""
            INSERT INTO currency (name, symbol) VALUES
                ('KZT', '₸'),
                ('USD', '$')
            ON CONFLICT (name) DO NOTHING;
        """)
        await session.execute(query)
        await session.commit()
        print("✅ Валюты успешно добавлены (или уже существуют).")

if __name__ == "__main__":
    asyncio.run(seed_currency())
