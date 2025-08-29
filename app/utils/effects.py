# -*- coding: utf-8 -*-
from typing import Optional
import asyncio
from aiogram import Bot
from aiogram.types import Message
try:
    from aiogram.enums import ChatAction  # aiogram v3
except Exception:
    class ChatAction:  # aiogram v2 fallback
        TYPING = "typing"

async def _send_typing(bot: Bot, chat_id: int, duration: float = 0.7) -> None:
    try:
        await bot.send_chat_action(chat_id, ChatAction.TYPING)
    except TypeError:
        await bot.send_chat_action(chat_id, action="typing")
    await asyncio.sleep(max(0.2, min(2.0, duration)))

async def send_with_effect(bot: Bot, chat_id: int, text: str, *, duration: float = 0.7, **kwargs):
    await _send_typing(bot, chat_id, duration)
    return await bot.send_message(chat_id, text, **kwargs)

async def edit_with_effect(message: Message, text: str, *, duration: float = 0.7, **kwargs):
    bot: Bot = message.bot
    await _send_typing(bot, message.chat.id, duration)
    try:
        return await message.edit_text(text, **kwargs)
    except Exception:
        return await bot.send_message(message.chat.id, text, **kwargs)
