# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.db import fetchall, fetchone, execute, get_setting
from app.keyboards import (
    admin_menu_kb,
    admin_prods_kb,
    admin_plans_prod_kb,
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

class PlanStates(StatesGroup):
    adding_title = State()
    adding_price = State()
    adding_desc = State()

class FindStates(StatesGroup):
    waiting_trk = State()

class BroadcastStates(StatesGroup):
    waiting_copy = State()
    waiting_forward = State()

# ---------- Admin Menu ----------
@router.callback_query(F.data == "admin:menu")
async def admin_menu(cb: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    try:
        await cb.message.edit_text("پنل مدیریت:", reply_markup=admin_menu_kb())
    except TelegramBadRequest:
        await cb.message.answer("پنل مدیریت:", reply_markup=admin_menu_kb())

# ---------- Products ----------
@router.callback_query(F.data == "admin:prods")
async def admin_prods(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    try:
        await cb.message.edit_text("📦 مدیریت محصولات:", reply_markup=admin_prods_kb(prods))
    except TelegramBadRequest:
        await cb.message.answer("📦 مدیریت محصولات:", reply_markup=admin_prods_kb(prods))

@router.callback_query(F.data == "admin:add_prod")
async def admin_add_prod(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(ProdStates.adding_title)
    try:
        await cb.message.edit_text("عنوان محصول را ارسال کنید (یا /cancel):")
    except TelegramBadRequest:
        await cb.message.answer("عنوان محصول را ارسال کنید (یا /cancel):")

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

@router.callback_query(F.data.startswith("admin:del_prod:"))
async def admin_del_prod(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    pid = int(cb.data.split(":")[2])
    await execute("DELETE FROM products WHERE id=?", pid)
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    try:
        await cb.message.edit_text("📦 مدیریت محصولات:", reply_markup=admin_prods_kb(prods))
    except TelegramBadRequest:
        await cb.message.answer("📦 مدیریت محصولات:", reply_markup=admin_prods_kb(prods))

# ---------- Plans ----------
@router.callback_query(F.data == "admin:plans")
async def admin_plans(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    if not prods:
        try:
            await cb.message.edit_text("هنوز محصولی ندارید. از «📦 محصولات» یک محصول اضافه کنید.", reply_markup=admin_menu_kb())
        except TelegramBadRequest:
            await cb.message.answer("هنوز محصولی ندارید. از «📦 محصولات» یک محصول اضافه کنید.", reply_markup=admin_menu_kb())
        return
    try:
        await cb.message.edit_text("یک محصول را برای مدیریت پلن‌ها انتخاب کنید:", reply_markup=admin_plans_prod_kb(prods))
    except TelegramBadRequest:
        await cb.message.answer("یک محصول را برای مدیریت پلن‌ها انتخاب کنید:", reply_markup=admin_plans_prod_kb(prods))

@router.callback_query(F.data.startswith("admin:plans_for_prod:"))
async def admin_plans_for_prod(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    pid = int(cb.data.split(":")[2])
    await state.update_data(prod_id=pid)
    plans = await fetchall("SELECT id, title, price FROM plans WHERE product_id=? ORDER BY price ASC", pid)
    txt = "💠 پلن‌های این محصول:\n" + ("(خالی)" if not plans else "\n".join([f"- {p['title']} | {p['price']:,} تومان" for p in plans]))
    try:
        await cb.message.edit_text(txt + "\n\nبرای افزودن پلن، عنوان را ارسال کنید.", reply_markup=admin_menu_kb())
    except TelegramBadRequest:
        await cb.message.answer(txt + "\n\nبرای افزودن پلن، عنوان را ارسال کنید.", reply_markup=admin_menu_kb())
    await state.set_state(PlanStates.adding_title)

@router.message(PlanStates.adding_title, F.text)
async def admin_add_plan_title(m: Message, state: FSMContext):
    title = (m.text or "").strip()
    if not title:
        await m.answer("❌ عنوان نامعتبر است.")
        return
    await state.update_data(plan_title=title)
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
    await m.answer("توضیح پلن را ارسال کنید (اختیاری). برای خالی گذاشتن /skip بزنید.")

@router.message(PlanStates.adding_desc, F.text.in_({'/skip','/SKIP'}))
async def admin_add_plan_desc_skip(m: Message, state: FSMContext):
    data = await state.get_data()
    prod_id = data.get("prod_id")
    title = data.get("plan_title")
    price = data.get("plan_price")
    await execute("INSERT INTO plans(product_id, title, price, description) VALUES(?,?,?,?)", prod_id, title, price, '')
    await state.clear()
    await m.answer("✅ پلن اضافه شد (بدون توضیح).", reply_markup=admin_menu_kb())

@router.message(PlanStates.adding_desc, F.text)
async def admin_add_plan_desc(m: Message, state: FSMContext):
    data = await state.get_data()
    prod_id = data.get("prod_id")
    title = data.get("plan_title")
    price = data.get("plan_price")
    desc = (m.text or "").strip()
    await execute("INSERT INTO plans(product_id, title, price, description) VALUES(?,?,?,?)", prod_id, title, price, desc)
    await state.clear()
    await m.answer("✅ پلن اضافه شد.", reply_markup=admin_menu_kb())

# ---------- Orders ----------
@router.callback_query(F.data == "admin:orders")
async def admin_orders(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    orders = await fetchall("SELECT id, status FROM orders ORDER BY id DESC LIMIT 20")
    try:
        await cb.message.edit_text("🧾 ۲۰ سفارش اخیر:", reply_markup=admin_orders_kb(orders))
    except TelegramBadRequest:
        await cb.message.answer("🧾 ۲۰ سفارش اخیر:", reply_markup=admin_orders_kb(orders))

@router.callback_query(F.data.startswith("admin:order_view:"))
async def admin_order_view(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    row = await fetchone("""SELECT o.id, o.status, o.tracking_code, p.title as plan_title, pr.title as product_title, p.price
                             FROM orders o
                             JOIN plans p ON p.id=o.plan_id
                             JOIN products pr ON pr.id=o.product_id
                             WHERE o.id=?""", oid)
    if not row:
        await cb.answer("سفارش یافت نشد.", show_alert=True)
        return
    txt = (f"سفارش #{row['id']}\nکد پیگیری: {row['tracking_code'] or '—'}\n"
           f"محصول: {row['product_title']}\nپلن: {row['plan_title']}\n"
           f"قیمت: {row['price']:,} تومان\nوضعیت: {row['status']}")
    try:
        await cb.message.edit_text(txt, reply_markup=admin_order_actions_kb(row['id']))
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=admin_order_actions_kb(row['id']))

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
            await cb.bot.send_message(row["tg_id"], "🔧")
            await cb.bot.send_message(row["tg_id"], f"🔧 سفارش شما با کد پیگیری {trk} در حال انجام است.")
        except Exception:
            pass
    await cb.answer("🔧 به حالت در حال انجام تغییر کرد")

@router.callback_query(F.data.startswith("admin:order_complete:"))
async def admin_order_complete(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    await execute("UPDATE orders SET status='completed' WHERE id=?", oid)
    row = await fetchone("SELECT tracking_code, u.tg_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", oid)
    trk = row["tracking_code"]or await _gen_tracking()
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
            await cb.bot.send_message(row["tg_id"], f"❌ سفارش شما با کد پیگیری {trk} رد شد. لطفاً با پشتیبانی در ارتباط باشید.")
        except Exception:
            pass
    await cb.answer("❌ سفارش رد شد")

# ---------- Find by tracking ----------
@router.callback_query(F.data == "admin:find_by_trk")
async def admin_find_by_trk_start(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(FindStates.waiting_trk)
    try:
        await cb.message.edit_text("کد پیگیری سفارش را ارسال کنید:", reply_markup=admin_menu_kb())
    except TelegramBadRequest:
        await cb.message.answer("کد پیگیری سفارش را ارسال کنید:", reply_markup=admin_menu_kb())

@router.message(FindStates.waiting_trk, F.text)
async def admin_find_by_trk_recv(m: Message, state: FSMContext):
    code = (m.text or "").strip().upper()
    await state.clear()
    row = await fetchone("""SELECT o.id, o.status, o.tracking_code, p.title as plan_title, pr.title as product_title, p.price
                             FROM orders o
                             JOIN plans p ON p.id=o.plan_id
                             JOIN products pr ON pr.id=o.product_id
                             WHERE o.tracking_code=?""", code)
    if not row:
        await m.answer("یافت نشد. مطمئنید کد پیگیری درست است؟", reply_markup=admin_menu_kb())
        return
    txt = (f"سفارش #{row['id']}\nکد پیگیری: {row['tracking_code']}\n"
           f"محصول: {row['product_title']}\nپلن: {row['plan_title']}\n"
           f"قیمت: {row['price']:,} تومان\nوضعیت: {row['status']}")
    await m.answer(txt, reply_markup=admin_order_actions_kb(row['id']))

# ---------- Broadcast ----------
@router.callback_query(F.data == "admin:broadcast_copy")
async def admin_broadcast_copy(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(BroadcastStates.waiting_copy)
    try:
        await cb.message.edit_text("پیامی که باید «کپی» شود را ارسال کنید.", reply_markup=admin_menu_kb())
    except TelegramBadRequest:
        await cb.message.answer("پیامی که باید «کپی» شود را ارسال کنید.", reply_markup=admin_menu_kb())

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
    try:
        await cb.message.edit_text("پیامی که باید «فوروارد» شود را ارسال کنید.", reply_markup=admin_menu_kb())
    except TelegramBadRequest:
        await cb.message.answer("پیامی که باید «فوروارد» شود را ارسال کنید.", reply_markup=admin_menu_kb())

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
