# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from app.utils.reactions import react_emoji
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.db import fetchall, fetchone, execute, get_setting
from app.keyboards import (
    admin_menu_kb,
    admin_settings_kb,
    admin_prods_kb,
    admin_plans_list_kb,
    admin_orders_kb,
    admin_order_actions_kb,
)

router = Router()

# ---------- Guards ----------
async def guard_admin(cb: CallbackQuery) -> bool:
    from app.config import settings
    admins = set(map(int, (settings.admins or "").split(","))) if isinstance(settings.admins, str) else set(settings.admins or [])
    ok = cb.from_user.id in admins
    if not ok:
        await cb.answer("مجوز دسترسی ندارید.", show_alert=True)
    return ok

# ---------- States ----------
class ProdStates(StatesGroup):
    adding_title = State()
    editing_title = State()

class PlanStates(StatesGroup):
    adding_title = State()
    adding_price = State()
    adding_desc = State()

class PlanEditStates(StatesGroup):
    editing_plan_id = State()
    editing_title = State()
    editing_price = State()
    editing_desc = State()

class FindStates(StatesGroup):
    waiting_trk = State()

class BroadcastStates(StatesGroup):
    waiting_copy = State()
    waiting_forward = State()

class SettingsStates(StatesGroup):
    editing_key = State()

# ---------- Helpers ----------
async def _safe_edit(message, text, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await message.answer(text, reply_markup=reply_markup)

async def _set_setting(key: str, value: str):
    await execute(
        """INSERT INTO settings(key, value) VALUES(?,?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        key, value
    )

def _label_for(key: str) -> str:
    return {
        "MAIN_CHANNEL": "کانال اصلی",
        "ORDER_CHANNEL": "کانال سفارش‌ها",
        "SUPPORT_USERNAME": "یوزرنیم پشتیبانی",
        "card_number": "شماره کارت",
        "WELCOME_TEXT": "متن خوش‌آمد",
    }.get(key, key)

# ---------- Admin Menu ----------
@router.callback_query(F.data == "admin:menu")
async def admin_menu(cb: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    await _safe_edit(cb.message, "پنل مدیریت:", reply_markup=admin_menu_kb())

# ---------- Settings (VIEW + EDIT) ----------
@router.callback_query(F.data == "admin:settings")
async def admin_settings(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    main_ch = await get_setting("MAIN_CHANNEL", "-")
    order_ch = await get_setting("ORDER_CHANNEL", "-")
    card = await get_setting("card_number", "-")
    welcome = await get_setting("WELCOME_TEXT", "-")
    support = await get_setting("SUPPORT_USERNAME", "-")
    txt = f"""⚙️ تنظیمات فعلی:
• کانال اصلی: {main_ch}
• کانال سفارش‌ها: {order_ch}
• شماره کارت: {card}
• پشتیبانی: {support}
• متن خوش‌آمد: {welcome}

برای ویرایش هر مورد، روی دکمه‌اش بزنید."""
    await _safe_edit(cb.message, txt, reply_markup=admin_settings_kb())

@router.callback_query(F.data.startswith("admin:set:"))
async def admin_settings_set(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    key = cb.data.split(":")[2]  # MAIN_CHANNEL / ORDER_CHANNEL / SUPPORT_USERNAME / CARD / WELCOME_TEXT
    if key == "CARD":
        key = "card_number"
    label = _label_for(key)
    await state.update_data(edit_key=key, edit_label=label)
    await state.set_state(SettingsStates.editing_key)
    await cb.message.answer(f"📝 مقدار جدید برای «{label}» را ارسال کنید:")

@router.message(SettingsStates.editing_key, F.text)
async def admin_settings_save(m: Message, state: FSMContext):
    data = await state.get_data()
    key = data.get("edit_key")
    label = data.get("edit_label") or key
    val = (m.text or "").strip()
    if not val:
        await m.answer("❌ مقدار نامعتبر است. دوباره ارسال کنید.")
        return
    # Normalize support username to start with @
    if key == "SUPPORT_USERNAME" and not val.startswith("@"):
        val = "@" + val
    await _set_setting(key, val)
    await state.clear()
    await m.answer(f"✅ «{label}» ذخیره شد.")
    # Show updated overview
    main_ch = await get_setting("MAIN_CHANNEL", "-")
    order_ch = await get_setting("ORDER_CHANNEL", "-")
    card = await get_setting("card_number", "-")
    welcome = await get_setting("WELCOME_TEXT", "-")
    support = await get_setting("SUPPORT_USERNAME", "-")
    txt = f"""⚙️ تنظیمات فعلی:
• کانال اصلی: {main_ch}
• کانال سفارش‌ها: {order_ch}
• شماره کارت: {card}
• پشتیبانی: {support}
• متن خوش‌آمد: {welcome}"""
    await m.answer(txt, reply_markup=admin_settings_kb())

# ---------- Products (CRUD) ----------
@router.callback_query(F.data == "admin:prods")
async def admin_prods(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    await _safe_edit(cb.message, "📦 مدیریت محصولات:", reply_markup=admin_prods_kb(prods))

@router.callback_query(F.data == "admin:add_prod")
async def admin_add_prod(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(ProdStates.adding_title)
    await cb.message.answer("عنوان محصول را ارسال کنید:")

@router.message(ProdStates.adding_title, F.text)
async def admin_add_prod_title(m: Message, state: FSMContext):
    title = (m.text or "").strip()
    if not title:
        await m.answer("❌ عنوان نامعتبر است.")
        return
    await execute("INSERT INTO products(title) VALUES(?)", title)
    await state.clear()
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    await m.answer("✅ محصول اضافه شد.", reply_markup=admin_prods_kb(prods))

@router.callback_query(F.data.startswith("admin:edit_prod:"))
async def admin_edit_prod(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    pid = int(cb.data.split(":")[2])
    await state.update_data(prod_id=pid)
    await state.set_state(ProdStates.editing_title)
    await cb.message.answer("✏️ عنوان جدید محصول را ارسال کنید:")

@router.message(ProdStates.editing_title, F.text)
async def admin_edit_prod_title(m: Message, state: FSMContext):
    title = (m.text or "").strip()
    if not title:
        await m.answer("❌ عنوان نامعتبر است.")
        return
    data = await state.get_data()
    pid = int(data.get("prod_id"))
    await execute("UPDATE products SET title=? WHERE id=?", title, pid)
    await state.clear()
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    await m.answer("✅ محصول ویرایش شد.", reply_markup=admin_prods_kb(prods))

@router.callback_query(F.data.startswith("admin:del_prod:"))
async def admin_del_prod(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    pid = int(cb.data.split(":")[2])
    await execute("DELETE FROM products WHERE id=?", pid)
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    await _safe_edit(cb.message, "📦 مدیریت محصولات:", reply_markup=admin_prods_kb(prods))

# ---------- Plans (CRUD) ----------
@router.callback_query(F.data == "admin:plans")
async def admin_plans(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    if not prods:
        await _safe_edit(cb.message, "هنوز محصولی ندارید. از «📦 محصولات» یک محصول اضافه کنید.", reply_markup=admin_menu_kb())
        return
    await _safe_edit(cb.message, "یک محصول را برای مدیریت پلن‌ها انتخاب کنید:", reply_markup=admin_prods_kb(prods))

@router.callback_query(F.data.startswith("admin:plans_for_prod:"))
async def admin_plans_for_prod(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    pid = int(cb.data.split(":")[2])
    await state.update_data(prod_id=pid)
    plans = await fetchall("SELECT id, title, price, description FROM plans WHERE product_id=? ORDER BY price ASC", pid)
    txt = "💠 پلن‌های این محصول:\n" + ("(خالی)" if not plans else "\n".join([f"- {p['title']} | {p['price']:,} تومان" for p in plans]))
    await _safe_edit(cb.message, txt, reply_markup=admin_plans_list_kb(plans, pid))

@router.callback_query(F.data.startswith("admin:add_plan:"))
async def admin_add_plan(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    pid = int(cb.data.split(":")[2])
    await state.update_data(prod_id=pid)
    await state.set_state(PlanStates.adding_title)
    await cb.message.answer("عنوان پلن را ارسال کنید:")

@router.message(PlanStates.adding_title, F.text)
async def admin_add_plan_title(m: Message, state: FSMContext):
    t = (m.text or "").strip()
    if not t:
        await m.answer("❌ عنوان نامعتبر است.")
        return
    await state.update_data(plan_title=t)
    await state.set_state(PlanStates.adding_price)
    await m.answer("قیمت پلن (تومان) را ارسال کنید (فقط عدد).")

@router.message(PlanStates.adding_price, F.text)
async def admin_add_plan_price(m: Message, state: FSMContext):
    price_text = (m.text or "").replace(",", "").strip()
    if not price_text.isdigit():
        await m.answer("❌ قیمت نامعتبر است. فقط عدد تومان ارسال کنید.")
        return
    await state.update_data(plan_price=int(price_text))
    await state.set_state(PlanStates.adding_desc)
    await m.answer("توضیح پلن را ارسال کنید.")

@router.message(PlanStates.adding_desc, F.text)
async def admin_add_plan_desc(m: Message, state: FSMContext):
    data = await state.get_data()
    pid = int(data.get("prod_id"))
    title = data.get("plan_title")
    price = int(data.get("plan_price"))
    desc = (m.text or "").strip()
    await execute("INSERT INTO plans(product_id, title, price, description) VALUES(?,?,?,?)", pid, title, price, desc)
    await state.clear()
    plans = await fetchall("SELECT id, title, price, description FROM plans WHERE product_id=? ORDER BY price ASC", pid)
    await m.answer("✅ پلن اضافه شد.", reply_markup=admin_plans_list_kb(plans, pid))

@router.callback_query(F.data.startswith("admin:edit_plan:"))
async def admin_edit_plan(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    plan_id = int(cb.data.split(":")[2])
    await state.update_data(edit_plan_id=plan_id)
    await state.set_state(PlanEditStates.editing_title)
    await cb.message.answer("✏️ عنوان جدید پلن را ارسال کنید:")

@router.message(PlanEditStates.editing_title, F.text)
async def plan_edit_title(m: Message, state: FSMContext):
    t = (m.text or "").strip()
    if not t:
        await m.answer("❌ عنوان نامعتبر است.")
        return
    data = await state.get_data()
    plid = int(data.get("edit_plan_id"))
    await execute("UPDATE plans SET title=? WHERE id=?", t, plid)
    await state.set_state(PlanEditStates.editing_price)
    await m.answer("💰 قیمت جدید (تومان) را ارسال کنید (فقط عدد).")

@router.message(PlanEditStates.editing_price, F.text)
async def plan_edit_price(m: Message, state: FSMContext):
    price_text = (m.text or "").replace(",", "").strip()
    if not price_text.isdigit():
        await m.answer("❌ قیمت نامعتبر است. فقط عدد تومان ارسال کنید.")
        return
    price = int(price_text)
    data = await state.get_data()
    plid = int(data.get("edit_plan_id"))
    await execute("UPDATE plans SET price=? WHERE id=?", price, plid)
    await state.set_state(PlanEditStates.editing_desc)
    await m.answer("📝 توضیح جدید پلن را ارسال کنید.")

@router.message(PlanEditStates.editing_desc, F.text)
async def plan_edit_desc(m: Message, state: FSMContext):
    desc = (m.text or "").strip()
    data = await state.get_data()
    plid = int(data.get("edit_plan_id"))
    await execute("UPDATE plans SET description=? WHERE id=?", desc, plid)
    row = await fetchone("SELECT product_id FROM plans WHERE id=?", plid)
    pid = int(row["product_id"]) if row else 0
    await state.clear()
    plans = await fetchall("SELECT id, title, price, description FROM plans WHERE product_id=? ORDER BY price ASC", pid)
    await m.answer("✅ پلن ویرایش شد.", reply_markup=admin_plans_list_kb(plans, pid))

@router.callback_query(F.data.startswith("admin:del_plan:"))
async def admin_del_plan(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    plid = int(cb.data.split(":")[2])
    row = await fetchone("SELECT product_id FROM plans WHERE id=?", plid)
    pid = int(row["product_id"]) if row else 0
    await execute("DELETE FROM plans WHERE id=?", plid)
    plans = await fetchall("SELECT id, title, price, description FROM plans WHERE product_id=? ORDER BY price ASC", pid)
    txt = "💠 پلن‌های این محصول:\n" + ("(خالی)" if not plans else "\n".join([f"- {p['title']} | {p['price']:,} تومان" for p in plans]))
    await _safe_edit(cb.message, txt, reply_markup=admin_plans_list_kb(plans, pid))

# ---------- Orders ----------
@router.callback_query(F.data == "admin:orders")
async def admin_orders(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    orders = await fetchall("SELECT id, status FROM orders ORDER BY id DESC LIMIT 20")
    await _safe_edit(cb.message, "🧾 ۲۰ سفارش اخیر:", reply_markup=admin_orders_kb(orders))

@router.callback_query(F.data.startswith("admin:order_view:"))
async def admin_order_view(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    row = await fetchone(
        """SELECT o.id, o.status, o.tracking_code,
                  p.title as plan_title, pr.title as product_title, p.price,
                  u.tg_id as user_tg, u.username as user_un
           FROM orders o
           JOIN plans p ON p.id=o.plan_id
           JOIN products pr ON pr.id=o.product_id
           JOIN users u ON u.id=o.user_id
           WHERE o.id=?""",
        oid
    )
    if not row:
        await cb.answer("سفارش یافت نشد.", show_alert=True)
        return

    txt = f"""سفارش #{row['id']}
کد پیگیری: {row['tracking_code'] or '—'}
کاربر: @{row['user_un'] or '-'}
آیدی عددی: {row['user_tg']}
محصول: {row['product_title']}
پلن: {row['plan_title']}
قیمت: {row['price']:,} تومان
وضعیت: {row['status']}"""

    await _safe_edit(cb.message, txt, reply_markup=admin_order_actions_kb(row['id']))


async def _gen_tracking():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.callback_query(F.data.startswith("admin:order_processing:"))
async def admin_order_processing(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    await execute("UPDATE orders SET status='processing' WHERE id=?", oid)
    row = await fetchone("SELECT tracking_code, u.tg_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", oid)
    trk = row["tracking_code"] or await _gen_tracking()
    if not row["tracking_code"]:
        await execute("UPDATE orders SET tracking_code=? WHERE id=?", trk, oid)
    if row and row["tg_id"]:
        try:
            await cb.bot.send_message(row["tg_id"], f"🔧 سفارش شما با کد پیگیری {trk} در حال انجام است.")
        except Exception:
            pass
    await cb.answer("🔧 وضعیت «در حال انجام» ثبت شد")
@router.callback_query(F.data.startswith("admin:order_complete:"))
async def admin_order_complete(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    await execute("UPDATE orders SET status='completed' WHERE id=?", oid)
    row = await fetchone("SELECT tracking_code, u.tg_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", oid)
    trk = row["tracking_code"] or await _gen_tracking()
    if not row["tracking_code"]:
        await execute("UPDATE orders SET tracking_code=? WHERE id=?", trk, oid)
    if row and row["tg_id"]:
        try:
            await cb.bot.send_message(row["tg_id"], "🎉")
            await cb.bot.send_message(row["tg_id"], f"🎉 سفارش شما با کد پیگیری {trk} انجام شد.")
        except Exception:
            pass
    await cb.answer("✅ اتمام کار ثبت شد")

@router.callback_query(F.data.startswith("admin:order_reject:"))
async def admin_order_reject(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    await execute("UPDATE orders SET status='rejected' WHERE id=?", oid)
    row = await fetchone("SELECT tracking_code, u.tg_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", oid)
    trk = row["tracking_code"] or await _gen_tracking()
    if not row["tracking_code"]:
        await execute("UPDATE orders SET tracking_code=? WHERE id=?", trk, oid)
    if row and row["tg_id"]:
        try:
            msg_rej = await cb.bot.send_message(row["tg_id"], f"❌ سفارش شما با کد پیگیری {trk} رد شد. لطفاً با پشتیبانی در ارتباط باشید.")
            try:
                await react_emoji(cb.bot, msg_rej.chat.id, msg_rej.message_id, "👎", big=True)
            except Exception:
                pass
        except Exception:
            pass
    await cb.answer("❌ سفارش رد شد")
@router.callback_query(F.data == "admin:find_by_trk")
async def admin_find_by_trk_start(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(FindStates.waiting_trk)
    await _safe_edit(cb.message, "کد پیگیری سفارش را ارسال کنید:", reply_markup=admin_menu_kb())

@router.message(FindStates.waiting_trk, F.text)
async def admin_find_by_trk_recv(m: Message, state: FSMContext):
    code = (m.text or "").strip().upper()
    await state.clear()
    row = await fetchone(
        """SELECT o.id, o.status, o.tracking_code,
                  p.title as plan_title, pr.title as product_title, p.price
           FROM orders o
           JOIN plans p ON p.id=o.plan_id
           JOIN products pr ON pr.id=o.product_id
           WHERE o.tracking_code=?""", code
    )
    if not row:
        await m.answer("یافت نشد. مطمئنید کد پیگیری درست است؟", reply_markup=admin_menu_kb())
        return
    txt = f"""سفارش #{row['id']}
کد پیگیری: {row['tracking_code']}
محصول: {row['product_title']}
پلن: {row['plan_title']}
قیمت: {row['price']:,} تومان
وضعیت: {row['status']}"""
    await m.answer(txt, reply_markup=admin_order_actions_kb(row['id']))

# ---------- Broadcast ----------
@router.callback_query(F.data == "admin:broadcast_copy")
async def admin_broadcast_copy(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(BroadcastStates.waiting_copy)
    await _safe_edit(cb.message, "پیامی که باید «کپی» شود را ارسال کنید.", reply_markup=admin_menu_kb())

@router.message(BroadcastStates.waiting_copy)
async def broadcast_copy_message(m: Message, state: FSMContext):
    users = await fetchall("SELECT tg_id FROM users WHERE tg_id IS NOT NULL")
    sent = 0
    for u in users:
        try:
            await m.bot.copy_message(chat_id=u["tg_id"], from_chat_id=m.chat.id, message_id=m.message_id)
            sent += 1
        except Exception:
            pass
    await state.clear()
    await m.answer(f"✅ ارسال کپی برای {sent} کاربر انجام شد.", reply_markup=admin_menu_kb())

@router.callback_query(F.data == "admin:broadcast_forward")
async def admin_broadcast_forward(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(BroadcastStates.waiting_forward)
    await _safe_edit(cb.message, "پیامی که باید «فوروارد» شود را ارسال کنید.", reply_markup=admin_menu_kb())

@router.message(BroadcastStates.waiting_forward)
async def broadcast_forward_message(m: Message, state: FSMContext):
    users = await fetchall("SELECT tg_id FROM users WHERE tg_id IS NOT NULL")
    sent = 0
    for u in users:
        try:
            await m.bot.forward_message(chat_id=u["tg_id"], from_chat_id=m.chat.id, message_id=m.message_id)
            sent += 1
        except Exception:
            pass
    await state.clear()
    await m.answer(f"✅ فوروارد برای {sent} کاربر انجام شد.", reply_markup=admin_menu_kb())
