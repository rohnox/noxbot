# -*- coding: utf-8 -*-
from typing import Optional, Sequence
from aiogram import Bot

# aiogram export paths differ by version; try both
try:
    from aiogram.types import ReactionTypeEmoji  # aiogram >=3.15
except Exception:  # pragma: no cover
    from aiogram.types.reaction_type_emoji import ReactionTypeEmoji  # fallback

async def react_emoji(bot: Bot, chat_id: int, message_id: int, emoji: str, big: bool = True) -> bool:
    """
    Set a reaction (emoji) on a specific message.
    Requires Bot API 7.0+ and bot permissions in the chat/channel.
    """
    try:
        await bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
            is_big=big,
        )
        return True
    except Exception:
        return False
