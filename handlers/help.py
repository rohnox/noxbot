from telegram import Update
from telegram.ext import ContextTypes
from database import get_lang
from locales.messages import t

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    await update.message.reply_text(t(lang, "help"))
