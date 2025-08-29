# -*- coding: utf-8 -*-
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.db import init_db
from app.handlers import start as start_handlers
from app.handlers import user_store, admin as admin_handlers

async def create_bot_and_dispatcher():
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN در env تنظیم نشده است.")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # ثبت روترها
    dp.include_router(start_handlers.router)
    dp.include_router(user_store.router)
    dp.include_router(admin_handlers.router)

    await init_db()
    logging.info("DB initialized and routers registered.")
    return bot, dp
