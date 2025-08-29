from telegram import Update
from telegram.ext import ContextTypes
from database import get_lang, list_orders
from locales.messages import t

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    rows = list_orders(None, limit=20, offset=0)
    # فهرست ساده‌ی کاربر: (فقط سفارش‌های خودش)
    rows = [r for r in rows if r[2] == uid]
    if not rows:
        await update.message.reply_text(t(lang, "orders_title") + "\n—")
        return
    lines = [f"#{code} — {status} — {amount/100}{currency}" for (oid, code, user_id, status, amount, currency, created) in rows]
    await update.message.reply_text(t(lang, "orders_title") + "\n" + "\n".join(lines))
