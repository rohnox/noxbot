from telegram import Update
from telegram.ext import ContextTypes
from database import upsert_user, get_lang
from locales.messages import t

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    upsert_user(user.id, user.first_name, user.last_name, user.username)
    lang = get_lang(user.id)
    await update.message.reply_text(t(lang, "welcome", name=user.first_name))
