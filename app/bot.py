# -*- coding: utf-8 -*-
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F
from aiogram.types import Message

from app.config import settings, is_admin
from app.db import init_db
from app.handlers import start as start_handlers
from app.handlers import user_store, admin as admin_handlers
from app.keyboards import main_menu

async def create_bot_and_dispatcher():
    await init_db()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())
    # Routers
    dp.include_router(start_handlers.router)
    dp.include_router(user_store.router)
    dp.include_router(admin_handlers.router)

    # Unknown commands -> show help (no silent fail)
    @dp.message(F.text.regexp(r"^/").as_("cmd"))
    async def unknown_command(m: Message, cmd):
        kb = main_menu(is_admin=is_admin(m.from_user.id))
        await m.answer("دستور ناشناس است. از دکمه‌ها استفاده کنید.", reply_markup=kb)

    return bot, dp
