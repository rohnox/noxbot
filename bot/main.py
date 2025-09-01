import asyncio
from aiogram import Bot, Dispatcher
from bot.handlers import start, catalog, cart_checkout, orders, support
from common.settings import Settings

settings = Settings()

async def main():
    bot = Bot(token=settings.BOT_TOKEN, parse_mode='HTML')
    dp = Dispatcher()
    dp.include_router(start)
    dp.include_router(catalog)
    dp.include_router(cart_checkout)
    dp.include_router(orders)
    dp.include_router(support)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
