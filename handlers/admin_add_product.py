from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from utils.decorators import admin_only
from database import create_product, update_product, add_license_codes
import random, re

TITLE, PRICE, CURRENCY, TYPE, ASSET = range(5)

def _sku_from_title(title: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
    return (s[:12] or 'p') + '-' + ''.join(random.choice('0123456789abcdef') for _ in range(6))

@admin_only
async def addproduct_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("عنوان محصول را وارد کنید:")
    return TITLE

@admin_only
async def addproduct_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text.strip()
    await update.message.reply_text("قیمت را وارد کنید (مثلاً 149000) — به واحد اصلی (بعداً ×100 می‌شود):")
    return PRICE

@admin_only
async def addproduct_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price_major = float(update.message.text.strip())
    except Exception:
        await update.message.reply_text("عدد معتبر وارد کنید.")
        return PRICE
    context.user_data['price_minor'] = int(round(price_major * 100))
    await update.message.reply_text("واحد پول (مثلاً USD):")
    return CURRENCY

@admin_only
async def addproduct_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = update.message.text.strip().upper()
    if len(cur) not in (3,4):
        await update.message.reply_text("واحد پول نامعتبر.")
        return CURRENCY
    context.user_data['currency'] = cur
    await update.message.reply_text("نوع تحویل را مشخص کنید: file یا license")
    return TYPE

@admin_only
async def addproduct_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tp = update.message.text.strip().lower()
    if tp not in ("file","license"):
        await update.message.reply_text("فقط 'file' یا 'license'.")
        return TYPE
    context.user_data['type'] = tp
    if tp == "file":
        await update.message.reply_text("فایل دیجیتال را به‌صورت Document ارسال کنید.")
        return ASSET
    else:
        await update.message.reply_text("کدهای لایسنس را هر خط یک کد ارسال کنید.")
        return ASSET

@admin_only
async def addproduct_asset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = context.user_data['title']
    price_minor = context.user_data['price_minor']
    currency = context.user_data['currency']
    tp = context.user_data['type']
    sku = _sku_from_title(title)

    file_id = None
    codes = None

    if tp == "file":
        if not update.message.document:
            await update.message.reply_text("فایل به‌صورت Document بفرستید.")
            return ASSET
        file_id = update.message.document.file_id
    else:
        codes = [line.strip() for line in (update.message.text or "").splitlines() if line.strip()]
        if not codes:
            await update.message.reply_text("حداقل یک کد لازم است.")
            return ASSET

    pid = create_product(sku=sku, title=title, description="", price=price_minor, currency=currency, delivery_type=tp, file_id=file_id, stock_count=None)
    if codes:
        n = add_license_codes(pid, codes)
        await update.message.reply_text(f"محصول #{pid} ایجاد شد و {n} کد اضافه شد.")
    else:
        await update.message.reply_text(f"محصول #{pid} ایجاد شد.")
    return ConversationHandler.END

@admin_only
async def addproduct_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END
