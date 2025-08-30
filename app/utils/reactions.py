from typing import Optional
from aiogram import Bot

async def react_emoji(bot: Bot, chat_id: int, message_id: int, emoji: str, big: bool = False) -> bool:
    """
    Safe reaction wrapper using setMessageReaction (Bot API >= 7.0).
    """
    try:
        await bot.call_api("setMessageReaction", {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}],
            "is_big": bool(big),
        })
        return True
    except Exception:
        return False
