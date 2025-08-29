from telegram import Update
from telegram.ext import ContextTypes
from database import get_lang, get_order_by_code, set_order_status, pop_license_code, get_product, order_items
from locales.messages import t
from utils.effects import send_with_confetti
from utils.logger import report_error_to_admins
from utils.time import fmt_ts_iso

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    order_code = update.message.successful_payment.invoice_payload
    order = get_order_by_code(order_code)
    if not order:
        await update.message.reply_text("Order not found.")
        return
    oid = order[0]

    set_order_status(oid, "paid")
    await send_with_confetti(context.bot, uid, t(lang, "paid"))
    # Deliver digital goods
    items = order_items(oid)
    for (product_id, quantity, unit_price, total_price) in items:
        prod = get_product(product_id)
        if not prod: continue
        (pid, sku, title, description, price, currency, delivery_type, file_id, stock_count, active) = prod
        if delivery_type == "file" and file_id:
            try:
                await context.bot.send_document(chat_id=uid, document=file_id, caption=title)
            except Exception as e:
                await report_error_to_admins(context.bot, f"Send file failed: {e}")
        elif delivery_type == "license":
            key = pop_license_code(product_id=pid)
            if not key:
                await context.bot.send_message(chat_id=uid, text=t(lang, "no_license"))
            else:
                await context.bot.send_message(chat_id=uid, text=f"{title}\nLicense: `{key}`", parse_mode="Markdown")
    set_order_status(oid, "delivered")
    await send_with_confetti(context.bot, uid, t(lang, "delivered"))

    # اطلاع به ادمین‌ها (Paid)
    from config import ADMIN_IDS, ADMIN_ALERT_CHAT_ID
    from locales.messages import t as T
    from utils.time import fmt_ts_iso
    o = get_order_by_code(order_code)
    text = T(lang, "admin_alert_paid", code=order_code, uid=uid, amount=o[4]/100, currency=o[5])
    targets = []
    if ADMIN_ALERT_CHAT_ID: targets.append(ADMIN_ALERT_CHAT_ID)
    elif ADMIN_IDS: targets.extend(ADMIN_IDS)
    for chat_id in targets:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            pass
