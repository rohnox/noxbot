# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hlink

from app.config import is_admin, settings
from app.db import upsert_user, get_setting
from app.keyboards import main_menu, back_home_kb
from app import texts

router = Router()

@router.message(CommandStart())
async def start_cmd(m: Message):
    await upsert_user(
        tg_id=m.from_user.id,
        first_name=m.from_user.first_name or "",
        username=m.from_user.username or "",
        is_admin=1 if is_admin(m.from_user.id) else 0,
    )
    welcome = await get_setting("welcome_text", settings.welcome_text or texts.WELCOME_FALLBACK)
    kb = main_menu(is_admin=is_admin(m.from_user.id))
    await m.answer(welcome, reply_markup=kb)

@router.callback_query(F.data == "home")
async def home_cb(c: CallbackQuery):
    welcome = await get_setting("welcome_text", settings.welcome_text or texts.WELCOME_FALLBACK)
    kb = main_menu(is_admin=is_admin(c.from_user.id))
    await c.message.edit_text(welcome, reply_markup=kb)

@router.callback_query(F.data == "account")
async def account_cb(c: CallbackQuery):
    txt = texts.ACCOUNT_TEXT
    await c.message.edit_text(txt, reply_markup=back_home_kb())

@router.callback_query(F.data == "support")
async def support_cb(c: CallbackQuery):
    sup = await get_setting("support_username", settings.support_username or "")
    sup = sup or settings.support_username or "support"
    txt = texts.SUPPORT_TEXT.format(username=sup)
    await c.message.edit_text(txt, reply_markup=back_home_kb())
