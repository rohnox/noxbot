# -*- coding: utf-8 -*-
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from app.db import get_setting
from app.config import settings

async def _resolve_channel():
    val = await get_setting("order_channel", settings.order_channel or "")
    return val or settings.order_channel

async def notify_order(bot: Bot, order_id: int, user_mention: str, product: str, plan: str, price: int) -> bool:
    channel = await _resolve_channel()
    if not channel:
        return False
    text = (
        f"#سفارش_{order_id}\n"
        f"کاربر: {user_mention}\n"
        f"محصول: {product}\n"
        f"پلن: {plan}\n"
        f"قیمت: {price:,} تومان\n"
        f"وضعیت: reviewing\n"
    )
    try:
        await bot.send_message(chat_id=channel, text=text, disable_web_page_preview=True)
        return True
    except TelegramBadRequest as e:
        print("Failed to send order notify:", e)
        return False
    except Exception as e:
        print("Failed to send order notify (generic):", e)
        return False
