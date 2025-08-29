
# NOTE: use ORDER_CHANNEL from env/config for any order channel notifications.
# -*- coding: utf-8 -*-
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from app.db import get_setting
from app.config import settings

async def _resolve_channel():
    val = await get_setting("order_channel", settings.order_channel or "")
    return val or settings.order_channel

async def notify_order(bot: Bot, order_id: int, user_mention: str, product: str, plan: str, price: int, tracking: str, user_id: int, username: str | None) -> bool:
    channel = await _resolve_channel()
    if not channel:
        return False
    text = (
        f"#سفارش_{order_id}\n"
        f"کد پیگیری: {tracking}\n"
        f"کاربر: {user_mention} (ID: {user_id}, @{username or '-'})\n"
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

async def notify_order_proof(bot: Bot, order_id: int, user_mention: str, product: str, plan: str, price: int, proof_type: str, proof_value: str) -> bool:
    channel = await _resolve_channel()
    if not channel:
        return False
    caption = (
        f"#سفارش_{order_id}\n"
        f"کاربر: {user_mention}\n"
        f"محصول: {product}\n"
        f"پلن: {plan}\n"
        f"قیمت: {price:,} تومان\n"
        f"وضعیت: reviewing\n"
        f"رسید: {proof_type or '—'}"
    )
    try:
        if proof_type == "photo" and proof_value:
            await bot.send_photo(chat_id=channel, photo=proof_value, caption=caption)
        else:
            text = caption + (f"\n\nمتن رسید:\n{proof_value}" if proof_value else "")
            await bot.send_message(chat_id=channel, text=text, disable_web_page_preview=True)
        return True
    except Exception as e:
        print("Failed to send order proof:", e)
        return False
