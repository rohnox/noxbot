from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from locales.messages import t
from database import get_user_count, list_user_ids
from utils.decorators import admin_only

BROADCAST = 1

@admin_only
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uc = get_user_count()
    await update.message.reply_text(f"Users: {uc}")

@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("متن برادکست را ارسال کنید. /cancel برای انصراف.")
    return BROADCAST

@admin_only
async def broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    from database import list_user_ids
    sent = 0
    for uid in list_user_ids():
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"برادکست به {sent} کاربر ارسال شد.")
    return ConversationHandler.END

@admin_only
async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END
