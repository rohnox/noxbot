from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import admin_only
from utils.keyboards import admin_main_keyboard, orders_list_keyboard, order_detail_keyboard, products_list_keyboard, product_admin_keyboard
from locales.messages import t
from database import get_user_count, list_orders, get_order, set_order_status, list_products, get_product, update_product
from utils.time import fmt_ts_iso

# ---- Admin entry
@admin_only
async def admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uc = get_user_count()
    oc = len(list_orders(None, 1000, 0))
    from database import revenue_sum
    rev = revenue_sum()
    await update.message.reply_text(t("fa", "admin_dashboard", uc=uc, oc=oc, rev=rev/100, cur="USD"), reply_markup=admin_main_keyboard())

@admin_only
async def admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ADM_DASH":
        uc = get_user_count()
        oc = len(list_orders(None, 1000, 0))
        from database import revenue_sum
        rev = revenue_sum()
        await query.edit_message_text(t("fa", "admin_dashboard", uc=uc, oc=oc, rev=rev/100, cur="USD"), reply_markup=admin_main_keyboard())
        return

    if data.startswith("ADM_ORDERS"):
        parts = data.split("_")
        page = 0
        if len(parts) == 4 and parts[2] == "PAGE":
            page = int(parts[3])
        limit = 10
        offset = page * limit
        rows = list_orders(None, limit=limit, offset=offset)
        order_pairs = [(r[0], r[1]) for r in rows]
        has_next = len(rows) == limit
        await query.edit_message_text("Orders:", reply_markup=orders_list_keyboard(order_pairs, page, has_next))
        return

    if data.startswith("ADM_ORDER_"):
        oid = int(data.split("_")[-1])
        o = get_order(oid)
        if not o:
            await query.edit_message_text("Not found")
            return
        (id, code, user_id, status, amount, currency, created, updated, paid, delivered, admin_notified) = o
        text = t("fa", "admin_order_detail", code=code, status=status, amount=amount/100, currency=currency,
                 created=fmt_ts_iso(created) if created else "-", paid=fmt_ts_iso(paid) if paid else "-", delivered=fmt_ts_iso(delivered) if delivered else "-", uid=user_id)
        await query.edit_message_text(text, reply_markup=order_detail_keyboard(oid))
        return

    if data.startswith("ADM_SET_"):
        parts = data.split("_")
        action = parts[2]
        oid = int(parts[3])
        status_map = {
            "PAID": "paid",
            "PROC": "processing",
            "DELIV": "delivered",
            "CANCEL": "canceled",
            "REF": "refunded",
        }
        new_status = status_map.get(action)
        if new_status:
            set_order_status(oid, new_status, note="by admin panel")
        await query.answer("OK")
        return

    if data.startswith("ADM_SEND_AGAIN_"):
        oid = int(data.split("_")[-1])
        from database import order_items
        o = get_order(oid)
        items = order_items(oid)
        for (product_id, quantity, unit_price, total_price) in items:
            prod = get_product(product_id)
            if prod and prod[6] == "file" and prod[7]:
                await context.bot.send_document(chat_id=o[2], document=prod[7], caption=prod[2])
        await query.answer("Sent")
        return

    if data == "ADM_PRODUCTS":
        prods = list_products(active_only=False)
        pairs = [(p[0], p[2]) for p in prods]
        await query.edit_message_text(t("fa", "admin_products_list"), reply_markup=products_list_keyboard(pairs))
        return

    if data == "ADM_ADD_PROD":
        await query.edit_message_text("برای افزودن محصول جدید دستور /addproduct را ارسال کنید.")
        return

    if data.startswith("ADM_PROD_"):
        pid = int(data.split("_")[-1])
        p = get_product(pid)
        if not p:
            await query.edit_message_text("Not found")
            return
        active = bool(p[9])
        await query.edit_message_text(f"{p[2]} — {p[4]/100} {p[5]} — type: {p[6]}", reply_markup=product_admin_keyboard(pid, active))
        return

    if data.startswith("ADM_TOGGLE_"):
        pid = int(data.split("_")[-1])
        p = get_product(pid)
        if p:
            new_active = 0 if p[9] == 1 else 1
            update_product(pid, active=new_active)
        await query.answer("Toggled")
        return

    if data.startswith("ADM_ADD_CODES_"):
        pid = int(data.split("_")[-1])
        context.user_data["add_codes_pid"] = pid
        context.user_data["await_codes"] = True
        await query.edit_message_text("کدهای لایسنس را هر خط یک کد ارسال کنید.")
        return
