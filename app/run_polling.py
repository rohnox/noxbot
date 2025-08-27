import asyncio
from aiogram import F
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI
from .bot import bot, dp
from .db import SessionLocal, engine, Base
from .handlers.user import router as user_router
from .handlers.admin import router as admin_router

# Middleware to inject DB session per update
@dp.update.outer_middleware()
class DBMiddleware:
    def __init__(self):
        pass
    async def __call__(self, handler, event, data):
        async with SessionLocal() as session:
            data['db'] = session
            result = await handler(event, data)
            return result

async def main():
    # init db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    print("Bot is running with polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
