import asyncio
import logging

from .bot import bot, dp
from .db import SessionLocal, engine, Base
from .handlers.user import router as user_router
from .handlers.admin import router as admin_router


class DBMiddleware:
    async def __call__(self, handler, event, data):
        # یک سشن Async به هر هندلر تزریق می‌کنیم
        async with SessionLocal() as session:
            data["db"] = session
            return await handler(event, data)


async def main():
    logging.basicConfig(level=logging.INFO)

    # ساخت جداول (در صورت نبود)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # رجیستر کردن میدل‌ویر و روترها
    dp.update.middleware(DBMiddleware())
    dp.include_router(user_router)
    dp.include_router(admin_router)

    print("Bot is running with polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
