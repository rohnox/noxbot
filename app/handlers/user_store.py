# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app import texts
from app.db import fetchall, fetchone, execute, get_or_create_user_id, get_setting
from app.config import settings
from app.keyboards import categories_kb, products_kb, plans_kb, pay_kb, proof_kb, back_home_kb
from app.services.orders import notify_order

router = Router()

class OrderStates(StatesGroup):
    waiting_proof = State()

@router.callback_query(F.data == "store")
async def store_cb(c: CallbackQuery):
    cats = await fetchall("SELECT id, title FROM categories ORDER BY id DESC")
    if not cats:
        await c.message.edit_text(texts.EMPTY_LIST, reply_markup=back_home_kb())
        return
    await c.message.edit_text(texts.STORE_CHOOSE_CATEGORY, reply_markup=categories_kb(cats))

@router.callback_query(F.data.startswith("cat:"))
async def category_pick(c: CallbackQuery):
    cat_id = int(c.data.split(":")[1])
    prods = await fetchall("SELECT id, title FROM products WHERE category_id=? ORDER BY id DESC", cat_id)
    if not prods:
        await c.message.edit_text(texts.EMPTY_LIST, reply_markup=back_home_kb())
        return
    await c.message.edit_text(texts.STORE_CHOOSE_PRODUCT, reply_markup=products_kb(prods, cat_id))

@router.callback_query(F.data.startswith("back:products:"))
async def back_to_products(c: CallbackQuery):
    prod_id = int(c.data.split(":")[2])
    row = await fetchone("SELECT category_id FROM products WHERE id=?", prod_id)
    if not row:
        await c.answer("نامعتبر", show_alert=True)
        return
    cat_id = int(row["category_id"])
    prods = await fetchall("SELECT id, title FROM products WHERE category_id=? ORDER BY id DESC", cat_id)
    await c.message.edit_text(texts.STORE_CHOOSE_PRODUCT, reply_markup=products_kb(prods, cat_id))

@router.callback_query(F.data.startswith("prod:"))
async def product_pick(c: CallbackQuery):
    prod_id = int(c.data.split(":")[1])
    plans = await fetchall("SELECT id, title, price FROM plans WHERE product_id=? ORDER BY price ASC", prod_id)
    if not plans:
        await c.message.edit_text(texts.EMPTY_LIST, reply_markup=back_home_kb())
        return
    await c.message.edit_text(texts.STORE_CHOOSE_PLAN, reply_markup=plans_kb(plans, prod_id))

@router.callback_query(F.data.startswith("plan:"))
async def plan_pick(c: CallbackQuery):
    plan_id = int(c.data.split(":")[1])
    plan = await fetchone("SELECT p.id as plan_id, p.title as plan_title, p.price, pr.title as product_title, pr.id as product_id FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?", plan_id)
    if not plan:
        await c.answer("نامعتبر", show_alert=True)
        return
    txt = texts.STORE_SUMMARY.format(product=plan["product_title"], plan=plan["plan_title"], price=plan["price"])
    await c.message.edit_text(txt, reply_markup=pay_kb(plan_id))

@router.callback_query(F.data.startswith("pay:"))
async def pay_cb(c: CallbackQuery, state: FSMContext):
    plan_id = int(c.data.split(":")[1])
    plan = await fetchone("SELECT p.id as plan_id, p.title as plan_title, p.price, pr.title as product_title, pr.id as product_id FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?", plan_id)
    if not plan:
        await c.answer("نامعتبر", show_alert=True)
        return
    tg_user_id = c.from_user.id
    user_id = await get_or_create_user_id(tg_user_id)
    order_id = await execute("INSERT INTO orders(user_id, product_id, plan_id, status) VALUES(?,?,?,?)",
                             user_id, plan["product_id"], plan_id, "awaiting_proof")

    # Notify channel immediately that a new order started (before proof)
    user_mention = f"<a href='tg://user?id={c.from_user.id}'>{c.from_user.first_name or 'user'}</a>"
    ok = await notify_order(c.bot, order_id, user_mention, plan["product_title"], plan["plan_title"], int(plan["price"]))
    card = await get_setting("card_number", settings.card_number or "")
    card = card or "—"
    info = texts.CARD_INFO.format(price=plan["price"], card=card)
    if not ok:
        info = "⚠️ اعلان به کانال سفارش‌ها ارسال نشد (ربات باید ادمین کانال باشد یا کانال درست تنظیم شود).\n\n" + info
    await c.message.edit_text(info, reply_markup=proof_kb(order_id))

@router.callback_query(F.data.startswith("proof:"))
async def proof_button(c: CallbackQuery, state: FSMContext):
    order_id = int(c.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(OrderStates.waiting_proof)
    await c.message.edit_text(texts.SEND_PROOF_PROMPT, reply_markup=back_home_kb())

@router.message(OrderStates.waiting_proof, F.photo)
async def proof_photo(m: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await m.answer("سفارش نامعتبر است.", reply_markup=back_home_kb())
        return
    photo = m.photo[-1]
    file_id = photo.file_id
    await execute("UPDATE orders SET proof_type=?, proof_value=?, status='reviewing' WHERE id=?", "photo", file_id, order_id)
    plan = await fetchone("""SELECT o.id, p.title as plan_title, p.price, pr.title as product_title, u.tg_id, u.first_name
                             FROM orders o
                             JOIN plans p ON p.id=o.plan_id
                             JOIN products pr ON pr.id=o.product_id
                             JOIN users u ON u.id=o.user_id WHERE o.id=?""", order_id)
    user_mention = f"<a href='tg://user?id={plan['tg_id']}'>{plan['first_name'] or 'user'}</a>"
    await notify_order(m.bot, order_id, user_mention, plan["product_title"], plan["plan_title"], int(plan["price"]))
    await m.answer(texts.PROOF_SAVED, reply_markup=back_home_kb())
    await state.clear()

@router.message(OrderStates.waiting_proof, F.text)
async def proof_text(m: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await m.answer("سفارش نامعتبر است.", reply_markup=back_home_kb())
        return
    await execute("UPDATE orders SET proof_type=?, proof_value=?, status='reviewing' WHERE id=?", "text", m.text, order_id)
    plan = await fetchone("""SELECT o.id, p.title as plan_title, p.price, pr.title as product_title, u.tg_id, u.first_name
                             FROM orders o
                             JOIN plans p ON p.id=o.plan_id
                             JOIN products pr ON pr.id=o.product_id
                             JOIN users u ON u.id=o.user_id WHERE o.id=?""", order_id)
    user_mention = f"<a href='tg://user?id={plan['tg_id']}'>{plan['first_name'] or 'user'}</a>"
    await notify_order(m.bot, order_id, user_mention, plan["product_title"], plan["plan_title"], int(plan["price"]))
    await m.answer(texts.PROOF_SAVED, reply_markup=back_home_kb())
    await state.clear()
