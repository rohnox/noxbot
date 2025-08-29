# -*- coding: utf-8 -*-
from aiogram import Bot
try:
    from aiogram.types import ReactionTypeEmoji
except Exception:  # pragma: no cover
    from aiogram.types.reaction_type_emoji import ReactionTypeEmoji

async def react_emoji(bot: Bot, chat_id: int, message_id: int, emoji: str, big: bool = True) -> bool:
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
