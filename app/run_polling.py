# -*- coding: utf-8 -*-
import asyncio
import logging
from app.bot import create_bot_and_dispatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

async def main():
    bot, dp = await create_bot_and_dispatcher()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
