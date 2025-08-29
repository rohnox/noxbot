from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import admin_only
from database import add_license_codes
from locales.messages import t

@admin_only
async def capture_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_codes"):
        return
    pid = context.user_data.get("add_codes_pid")
    codes = [line.strip() for line in (update.message.text or "").splitlines() if line.strip()]
    n = add_license_codes(pid, codes)
    context.user_data["await_codes"] = False
    await update.message.reply_text(t("fa", "admin_codes_added", n=n))
