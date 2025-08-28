# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.config import is_admin, settings
from app.db import upsert_user, get_setting, fetchone
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
    main_channel = await get_setting("main_channel", settings.main_channel or "")
    main_channel_url = f"https://t.me/{main_channel.lstrip('@')}" if main_channel else None
    kb = main_menu(is_admin=is_admin(m.from_user.id), main_channel_url=main_channel_url)
    await m.answer(welcome, reply_markup=kb)

@router.callback_query(F.data == "home")
async def home_cb(c: CallbackQuery):
    welcome = await get_setting("welcome_text", settings.welcome_text or texts.WELCOME_FALLBACK)
    main_channel = await get_setting("main_channel", settings.main_channel or "")
    main_channel_url = f"https://t.me/{main_channel.lstrip('@')}" if main_channel else None
    kb = main_menu(is_admin=is_admin(c.from_user.id), main_channel_url=main_channel_url)
    await c.message.edit_text(welcome, reply_markup=kb)

@router.callback_query(F.data == "account")
async def account_cb(c: CallbackQuery):
    me = await fetchone("SELECT id FROM users WHERE tg_id=?", c.from_user.id)
    uid = me["id"] if me else 0
    stats = await fetchone("""
        SELECT 
          (SELECT COUNT(1) FROM orders WHERE user_id=?) as total,
          (SELECT COUNT(1) FROM orders WHERE user_id=? AND status='approved') as ok,
          (SELECT COUNT(1) FROM orders WHERE user_id=? AND status IN ('awaiting_proof','reviewing')) as review
    """, uid, uid, uid)
    txt = texts.ACCOUNT_TEXT.format(
        id=c.from_user.id,
        name=c.from_user.first_name or '-',
        username=(c.from_user.username or '-'),
        orders_total=(stats["total"] if stats else 0),
        orders_ok=(stats["ok"] if stats else 0),
        orders_review=(stats["review"] if stats else 0),
    )
    await c.message.edit_text(txt, reply_markup=back_home_kb())

@router.callback_query(F.data == "support")
async def support_cb(c: CallbackQuery):
    sup = await get_setting("support_username", settings.support_username or "")
    sup = sup or settings.support_username or "support"
    txt = texts.SUPPORT_TEXT.format(username=sup)
    await c.message.edit_text(txt, reply_markup=back_home_kb())
