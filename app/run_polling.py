# -*- coding: utf-8 -*-
import asyncio
import logging
from app.bot import create_bot_and_dispatcher

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)

async def main():
    bot, dp = await create_bot_and_dispatcher()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
