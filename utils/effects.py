from telegram import ReactionTypeEmoji

CONFETTI = "🎉"

async def send_with_confetti(bot, chat_id: int, text: str, **kwargs):
    """ارسال پیام + ری‌اکشن متحرک 🎉 (در صورت پشتیبانی کلاینت).
    اگر setMessageReaction در کلاینت پشتیبانی نشود، فقط پیام ارسال می‌شود.
    """
    msg = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    try:
        await bot.set_message_reaction(
            chat_id=chat_id,
            message_id=msg.message_id,
            reaction=[ReactionTypeEmoji(CONFETTI)],
            is_big=True,  # انیمیشن بزرگ
        )
    except Exception:
        pass
    return msg
