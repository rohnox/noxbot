# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app import texts
from app.config import is_admin, settings
from app.db import fetchall, fetchone, execute, set_setting, get_setting
from app.keyboards import (
    admin_menu_kb, admin_cats_kb, admin_prods_cats_kb, admin_prods_kb,
    admin_plans_prod_kb, admin_plans_kb, admin_settings_kb,
    admin_orders_kb, admin_order_actions_kb, main_menu
)

router = Router()

# ---- States ----
class CatStates(StatesGroup):
    adding = State()

class ProdStates(StatesGroup):
    adding_title = State()
    add_cat_id = State()

class PlanStates(StatesGroup):
    adding_title = State()
    adding_price = State()
    add_prod_id = State()

class SettingsStates(StatesGroup):
    set_welcome = State()
    set_support = State()
    set_card = State()
    set_channel = State()

class BroadcastStates(StatesGroup):
    copy_all = State()
    forward_all = State()

# ---- Access guard ----
async def guard_admin(cb: CallbackQuery) -> bool:
    if not is_admin(cb.from_user.id):
        await cb.answer(texts.ADMIN_NEED, show_alert=True)
        return False
    return True

# ---- Menu ----
@router.callback_query(F.data == "admin:menu")
async def admin_menu(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    await cb.message.edit_text(texts.ADMIN_MENU_TEXT, reply_markup=admin_menu_kb())

# ---- Categories ----
@router.callback_query(F.data == "admin:cats")
async def admin_cats(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    cats = await fetchall("SELECT id, title FROM categories ORDER BY id DESC")
    await cb.message.edit_text("مدیریت دسته‌ها:", reply_markup=admin_cats_kb(cats))

@router.callback_query(F.data == "admin:add_cat")
async def admin_add_cat(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(CatStates.adding)
    await cb.message.edit_text("عنوان دسته جدید را ارسال کنید (یا /cancel):")

@router.message(CatStates.adding, F.text)
async def admin_add_cat_title(m: Message, state: FSMContext):
    title = (m.text or "").strip()
    if not title:
        await m.answer("عنوان نامعتبر است. دوباره ارسال کنید.")
        return
    await execute("INSERT INTO categories(title) VALUES(?)", title)
    await state.clear()
    await m.answer("✅ دسته اضافه شد.", reply_markup=admin_menu_kb())

@router.callback_query(F.data.startswith("admin:del_cat:"))
async def admin_del_cat(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    cat_id = int(cb.data.split(":")[2])
    await execute("DELETE FROM categories WHERE id=?", cat_id)
    await admin_cats(cb)

# ---- Products ----
@router.callback_query(F.data == "admin:prods")
async def admin_prods(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    cats = await fetchall("SELECT id, title FROM categories ORDER BY id DESC")
    if not cats:
        await cb.message.edit_text("ابتدا دسته اضافه کنید.", reply_markup=admin_menu_kb())
        return
    await cb.message.edit_text("یک دسته را برای مدیریت محصولات انتخاب کنید:", reply_markup=admin_prods_cats_kb(cats))

@router.callback_query(F.data.startswith("admin:prods_cat:"))
async def admin_prods_for_cat(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    cat_id = int(cb.data.split(":")[2])
    prods = await fetchall("SELECT id, title FROM products WHERE category_id=? ORDER BY id DESC", cat_id)
    await cb.message.edit_text("مدیریت محصولات:", reply_markup=admin_prods_kb(prods, cat_id))

@router.callback_query(F.data.startswith("admin:add_prod:"))
async def admin_add_prod(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    cat_id = int(cb.data.split(":")[2])
    await state.update_data(cat_id=cat_id)
    await state.set_state(ProdStates.adding_title)
    await cb.message.edit_text("عنوان محصول را ارسال کنید (یا /cancel):")

@router.message(ProdStates.adding_title, F.text)
async def admin_add_prod_title(m: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("cat_id")
    title = (m.text or "").strip()
    if not title:
        await m.answer("عنوان نامعتبر است.")
        return
    await execute("INSERT INTO products(category_id, title) VALUES(?,?)", cat_id, title)
    await state.clear()
    await m.answer("✅ محصول اضافه شد.", reply_markup=admin_menu_kb())

@router.callback_query(F.data.startswith("admin:del_prod:"))
async def admin_del_prod(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    pid = int(cb.data.split(":")[2])
    await execute("DELETE FROM products WHERE id=?", pid)
    await admin_prods(cb)

# ---- Plans ----
@router.callback_query(F.data == "admin:plans")
async def admin_plans(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    if not prods:
        await cb.message.edit_text("ابتدا محصول اضافه کنید.", reply_markup=admin_menu_kb())
        return
    await cb.message.edit_text("محصول را انتخاب کنید:", reply_markup=admin_plans_prod_kb(prods))

@router.callback_query(F.data.startswith("admin:plans_prod:"))
async def admin_plans_for_prod(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    prod_id = int(cb.data.split(":")[2])
    plans = await fetchall("SELECT id, title, price FROM plans WHERE product_id=? ORDER BY price ASC", prod_id)
    await cb.message.edit_text("مدیریت پلن‌ها:", reply_markup=admin_plans_kb(plans, prod_id))

@router.callback_query(F.data.startswith("admin:add_plan:"))
async def admin_add_plan(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    prod_id = int(cb.data.split(":")[2])
    await state.update_data(prod_id=prod_id)
    await state.set_state(PlanStates.adding_title)
    await cb.message.edit_text("عنوان پلن را ارسال کنید (یا /cancel):")

@router.message(PlanStates.adding_title, F.text)
async def admin_add_plan_title(m: Message, state: FSMContext):
    title = (m.text or "").strip()
    if not title:
        await m.answer("عنوان نامعتبر است.")
        return
    await state.update_data(plan_title=title)
    await state.set_state(PlanStates.adding_price)
    await m.answer("قیمت پلن (تومان) را ارسال کنید:")

@router.message(PlanStates.adding_price, F.text)
async def admin_add_plan_price(m: Message, state: FSMContext):
    try:
        price = int((m.text or "").replace(",", "").strip())
    except ValueError:
        await m.answer("قیمت نامعتبر است. فقط عدد ارسال کنید.")
        return
    data = await state.get_data()
    prod_id = data.get("prod_id")
    title = data.get("plan_title")
    await execute("INSERT INTO plans(product_id, title, price) VALUES(?,?,?)", prod_id, title, price)
    await state.clear()
    await m.answer("✅ پلن اضافه شد.", reply_markup=admin_menu_kb())

@router.callback_query(F.data.startswith("admin:del_plan:"))
async def admin_del_plan(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    plan_id = int(cb.data.split(":")[2])
    await execute("DELETE FROM plans WHERE id=?", plan_id)
    await admin_plans(cb)

# ---- Orders ----
@router.callback_query(F.data == "admin:orders")
async def admin_orders(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    rows = await fetchall("SELECT id, status FROM orders ORDER BY id DESC LIMIT 20")
    await cb.message.edit_text("آخرین سفارش‌ها:", reply_markup=admin_orders_kb(rows))

@router.callback_query(F.data.startswith("admin:order:"))
async def admin_order_details(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    row = await fetchone("""SELECT o.id, o.status, o.proof_type, o.proof_value, p.title as plan_title, p.price,
                                   pr.title as product_title, u.tg_id, u.first_name
                            FROM orders o
                            JOIN plans p ON p.id=o.plan_id
                            JOIN products pr ON pr.id=o.product_id
                            JOIN users u ON u.id=o.user_id
                            WHERE o.id=?""", oid)
    if not row:
        await cb.answer("یافت نشد.", show_alert=True)
        return
    txt = (f"سفارش #{row['id']}\n"
           f"کاربر: <a href='tg://user?id={row['tg_id']}'>{row['first_name'] or 'user'}</a>\n"
           f"محصول: {row['product_title']}\n"
           f"پلن: {row['plan_title']}\n"
           f"قیمت: {row['price']:,} تومان\n"
           f"وضعیت: {row['status']}\n"
           f"رسید: {row['proof_type'] or '—'}")
    await cb.message.edit_text(txt, reply_markup=admin_order_actions_kb(oid))

@router.callback_query(F.data.startswith("admin:order_approve:"))
async def admin_order_approve(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    await execute("UPDATE orders SET status='approved' WHERE id=?", oid)
    # notify user
    row = await fetchone("SELECT u.tg_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", oid)
    if row:
        try:
            await cb.bot.send_message(row["tg_id"], texts.ORDER_APPROVED_USER)
        except Exception:
            pass
    await cb.answer("✅ تایید شد")
    await admin_orders(cb)

@router.callback_query(F.data.startswith("admin:order_reject:"))
async def admin_order_reject(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    oid = int(cb.data.split(":")[2])
    await execute("UPDATE orders SET status='rejected' WHERE id=?", oid)
    # notify user
    row = await fetchone("SELECT u.tg_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", oid)
    if row:
        try:
            await cb.bot.send_message(row["tg_id"], texts.ORDER_REJECTED_USER)
        except Exception:
            pass
    await cb.answer("❌ رد شد")
    await admin_orders(cb)

# ---- Settings ----
@router.callback_query(F.data == "admin:settings")
async def admin_settings(cb: CallbackQuery):
    if not await guard_admin(cb):
        return
    await cb.message.edit_text("تنظیمات:", reply_markup=admin_settings_kb())

@router.callback_query(F.data == "admin:set:welcome")
async def admin_set_welcome(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(SettingsStates.set_welcome)
    await cb.message.edit_text(texts.SET_WELCOME_PROMPT)

@router.message(SettingsStates.set_welcome, F.text)
async def admin_set_welcome_text(m: Message, state: FSMContext):
    await set_setting("welcome_text", m.text)
    await state.clear()
    await m.answer("✅ متن خوش‌آمدگویی ذخیره شد.", reply_markup=admin_menu_kb())

@router.callback_query(F.data == "admin:set:support")
async def admin_set_support(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(SettingsStates.set_support)
    await cb.message.edit_text(texts.SET_SUPPORT_PROMPT)

@router.message(SettingsStates.set_support, F.text)
async def admin_set_support_text(m: Message, state: FSMContext):
    await set_setting("support_username", m.text.strip().lstrip("@"))
    await state.clear()
    await m.answer("✅ پشتیبانی ذخیره شد.", reply_markup=admin_menu_kb())

@router.callback_query(F.data == "admin:set:card")
async def admin_set_card(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(SettingsStates.set_card)
    await cb.message.edit_text(texts.SET_CARD_PROMPT)

@router.message(SettingsStates.set_card, F.text)
async def admin_set_card_text(m: Message, state: FSMContext):
    await set_setting("card_number", m.text.strip())
    await state.clear()
    await m.answer("✅ شماره کارت ذخیره شد.", reply_markup=admin_menu_kb())

@router.callback_query(F.data == "admin:set:channel")
async def admin_set_channel(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(SettingsStates.set_channel)
    await cb.message.edit_text(texts.SET_CHANNEL_PROMPT)

@router.message(SettingsStates.set_channel, F.text)
async def admin_set_channel_text(m: Message, state: FSMContext):
    await set_setting("order_channel", m.text.strip())
    await state.clear()
    await m.answer("✅ کانال سفارش‌ها ذخیره شد.", reply_markup=admin_menu_kb())

# ---- Broadcast ----
@router.callback_query(F.data == "admin:broadcast_copy")
async def admin_broadcast_copy(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(BroadcastStates.copy_all)
    await cb.message.edit_text(texts.BROADCAST_COPY_PROMPT)

@router.message(BroadcastStates.copy_all)
async def admin_broadcast_copy_message(m: Message, state: FSMContext):
    # send copy to all users
    users = await fetchall("SELECT tg_id FROM users ORDER BY id DESC")
    sent = 0
    for u in users:
        try:
            await m.copy_to(u["tg_id"])
            sent += 1
        except Exception:
            pass
    await state.clear()
    await m.answer(texts.BROADCAST_DONE.format(n=sent), reply_markup=admin_menu_kb())

@router.callback_query(F.data == "admin:broadcast_forward")
async def admin_broadcast_forward(cb: CallbackQuery, state: FSMContext):
    if not await guard_admin(cb):
        return
    await state.set_state(BroadcastStates.forward_all)
    await cb.message.edit_text(texts.BROADCAST_FORWARD_PROMPT)

@router.message(BroadcastStates.forward_all)
async def admin_broadcast_forward_message(m: Message, state: FSMContext):
    users = await fetchall("SELECT tg_id FROM users ORDER BY id DESC")
    sent = 0
    for u in users:
        try:
            await m.forward(chat_id=u["tg_id"])
            sent += 1
        except Exception:
            pass
    await state.clear()
    await m.answer(texts.BROADCAST_DONE.format(n=sent), reply_markup=admin_menu_kb())
