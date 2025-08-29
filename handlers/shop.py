import random, string
from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from database import list_products, get_lang, get_product, create_order, add_order_item, set_order_status, get_order_by_code
from locales.messages import t
from utils.keyboards import store_list_keyboard, product_keyboard
from utils.effects import send_with_confetti
from utils.logger import report_error_to_admins
from config import PAYMENT_PROVIDER_TOKEN, CURRENCY, ADMIN_IDS, ADMIN_ALERT_CHAT_ID
from utils.time import fmt_ts_iso

def _short_code(n=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

async def store_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    prods = list_products(active_only=True)
    if not prods:
        await update.message.reply_text(t(lang, "store_empty"))
        return
    items = [(p[0], p[2]) for p in prods]  # (id, title)
    await update.message.reply_text("🛍️", reply_markup=store_list_keyboard(items))

async def store_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "STORE_BACK":
        await store_cmd(update, context)
        return

    if data.startswith("VIEW_"):
        pid = int(data.split("_", 1)[1])
        prod = get_product(pid)
        if not prod:
            await query.edit_message_text("Not found")
            return
        (pid, sku, title, description, price, currency, delivery_type, file_id, stock_count, active) = prod
        uid = update.effective_user.id
        lang = get_lang(uid)
        text = f"{title}\n\n{description or ''}\n\n" + t(lang, "product_price", price=price/100, currency=currency)
        await query.edit_message_text(text, reply_markup=product_keyboard(pid))
        return

    if data.startswith("BUY_"):
        pid = int(data.split("_", 1)[1])
        prod = get_product(pid)
        if not prod:
            await query.edit_message_text("Not found")
            return
        (pid, sku, title, description, price, currency, delivery_type, file_id, stock_count, active) = prod
        uid = update.effective_user.id
        lang = get_lang(uid)

        # ایجاد سفارش + فاکتور
        code = _short_code()
        oid = create_order(code=code, user_id=uid, amount=price, currency=currency)
        add_order_item(order_id=oid, product_id=pid, quantity=1, unit_price=price)
        set_order_status(oid, "invoice_sent")

        await send_with_confetti(context.bot, uid, t(lang, "order_created", code=code))
        await context.bot.send_invoice(
            chat_id=uid,
            title=title,
            description=description or title,
            payload=code,
            provider_token=PAYMENT_PROVIDER_TOKEN or "TEST",
            currency=currency or CURRENCY,
            prices=[LabeledPrice(title, price)],
            is_flexible=False,
        )
        await context.bot.send_message(chat_id=uid, text=t(lang, "invoice_sent"))

        # اعلان یک‌پارچه به ادمین‌ها
        from database import get_order_by_code
        o = get_order_by_code(code)
        ts = fmt_ts_iso(o[6])
        text = t(lang, "admin_alert_new_order", code=code, uid=uid, title=title, amount=price/100, currency=currency, ts=ts)
        targets = []
        if ADMIN_ALERT_CHAT_ID: targets.append(ADMIN_ALERT_CHAT_ID)
        elif ADMIN_IDS: targets.extend(ADMIN_IDS)
        for chat_id in targets:
            try:
                await context.bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                pass
        return
