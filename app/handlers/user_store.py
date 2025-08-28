# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app import texts
from app.db import fetchall, fetchone, execute, get_or_create_user_id, get_setting
from app.config import settings
from app.keyboards import products_kb, plans_kb, pay_kb, proof_kb, back_home_kb
from app.services.orders import notify_order, notify_order_proof

router = Router()

def _gen_tracking():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class OrderStates(StatesGroup):
    waiting_proof = State()

@router.callback_query(F.data == "store")
async def store_cb(c: CallbackQuery):
    # مستقیم محصولات را لیست کن (بدون دسته‌بندی)
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    if not prods:
        await c.message.edit_text(texts.EMPTY_LIST, reply_markup=back_home_kb())
        return
    # reuse products_kb; cat_id argument removed, adapt signature
    await c.message.edit_text("یک محصول را انتخاب کنید:", reply_markup=products_kb(prods))

@router.callback_query(F.data.startswith("prod:"))
async def product_pick(c: CallbackQuery):
    prod_id = int(c.data.split(":")[1])
    plans = await fetchall("SELECT id, title, price FROM plans WHERE product_id=? ORDER BY price ASC", prod_id)
    if not plans:
        await c.message.edit_text(texts.EMPTY_LIST, reply_markup=back_home_kb())
        return
    await c.message.edit_text(texts.STORE_CHOOSE_PLAN, reply_markup=plans_kb(plans, prod_id))

@router.callback_query(F.data.startswith("plan:"))
async def plan_pick(c: CallbackQuery, state: FSMContext):
    plan_id = int(c.data.split(":")[1])
    plan = await fetchone("SELECT p.id as plan_id, p.title as plan_title, p.price, p.description, pr.title as product_title, pr.id as product_id FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?", plan_id)
    if not plan:
        await c.answer("نامعتبر", show_alert=True)
        return
    await state.update_data(plan_id=plan_id, product_id=plan["product_id"], note=None)
    desc = (plan['description'] or '').strip()
    txt = texts.STORE_SUMMARY.format(product=plan["product_title"], plan=plan["plan_title"], price=plan["price"]) + (f"\n\n📝 توضیح پلن: {desc}" if desc else '') + "\\n\\n" + texts.CONTINUE_TO_PAY
    await c.message.edit_text(txt, reply_markup=pay_kb(plan_id))

@router.callback_query(F.data.regexp(r"^pay:(\d+)$"))
async def pay_cb(c: CallbackQuery, state: FSMContext):
    plan_id = int(c.data.split(":")[1])
    plan = await fetchone("SELECT p.id as plan_id, p.title as plan_title, p.price, p.description, pr.title as product_title, pr.id as product_id FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?", plan_id)
    if not plan:
        await c.answer("نامعتبر", show_alert=True)
        return
    data = await state.get_data()
    note = (data or {}).get("note")
    tg_user_id = c.from_user.id
    user_id = await get_or_create_user_id(tg_user_id)
    trk = _gen_tracking()
    order_id = await execute("INSERT INTO orders(user_id, product_id, plan_id, status, tracking_code) VALUES(?,?,?,?,?)",
                             user_id, plan["product_id"], plan_id, "awaiting_proof", note)
    # اعلان اولیه سفارش
    mention = f"<a href='tg://user?id={c.from_user.id}'>{c.from_user.first_name or 'user'}</a>"
    ok = await notify_order(c.bot, order_id, mention, plan["product_title"], plan["plan_title"], int(plan["price"]), trk, c.from_user.id, c.from_user.username)
    card = await get_setting("card_number", settings.card_number or "")
    card = card or "—"
    info = texts.TRACKING_ASSIGNED.format(trk=trk) + "\n\n" + texts.CARD_INFO.format(price=plan["price"], card=card)
    if note:
        info += f"\\n\\nتوضیح شما: {note}"
    if not ok:
        info = "⚠️ اعلان به کانال سفارش‌ها ارسال نشد (ربات باید ادمین کانال باشد یا کانال درست تنظیم شود).\\n\\n" + info
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
    file_id = m.photo[-1].file_id
    await execute("UPDATE orders SET proof_type=?, proof_value=?, status='reviewing' WHERE id=?", "photo", file_id, order_id)
    plan = await fetchone("""SELECT o.id, o.tracking_code, p.title as plan_title, p.price, pr.title as product_title, u.tg_id, u.first_name, u.username
                             FROM orders o
                             JOIN plans p ON p.id=o.plan_id
                             JOIN products pr ON pr.id=o.product_id
                             JOIN users u ON u.id=o.user_id WHERE o.id=?""", order_id)
    user_mention = f"<a href='tg://user?id={plan['tg_id']}'>{plan['first_name'] or 'user'}</a> (@{plan['username'] or '-'})"
    await notify_order_proof(m.bot, order_id, user_mention, plan["product_title"], plan["plan_title"], int(plan["price"]), plan['tracking_code'], plan['tg_id'], plan['username'], "photo", file_id)
    if plan["note"]:
        try:
            await m.bot.send_message(chat_id=await get_setting("order_channel", None), text=f"📝 توضیح کاربر برای #سفارش_{order_id}:\n{plan['note']}")
        except Exception:
            pass
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
    plan = await fetchone("""SELECT o.id, o.tracking_code, p.title as plan_title, p.price, pr.title as product_title, u.tg_id, u.first_name, u.username
                             FROM orders o
                             JOIN plans p ON p.id=o.plan_id
                             JOIN products pr ON pr.id=o.product_id
                             JOIN users u ON u.id=o.user_id WHERE o.id=?""", order_id)
    user_mention = f"<a href='tg://user?id={plan['tg_id']}'>{plan['first_name'] or 'user'}</a> (@{plan['username'] or '-'})"
    await notify_order_proof(m.bot, order_id, user_mention, plan["product_title"], plan["plan_title"], int(plan["price"]), plan['tracking_code'], plan['tg_id'], plan['username'], "text", m.text)
    if plan["note"]:
        try:
            await m.bot.send_message(chat_id=await get_setting("order_channel", None), text=f"📝 توضیح کاربر برای #سفارش_{order_id}:\n{plan['note']}")
        except Exception:
            pass
    await m.answer(texts.PROOF_SAVED, reply_markup=back_home_kb())
    await state.clear()


@router.callback_query(F.data == "orders:mine")
async def my_orders(c: CallbackQuery):
    rows = await fetchall("SELECT o.id, o.tracking_code, o.status FROM orders o JOIN users u ON u.id=o.user_id WHERE u.tg_id=? ORDER BY o.id DESC LIMIT 5", c.from_user.id)
    if not rows:
        await c.message.edit_text("هیچ سفارشی ثبت نکرده‌اید.", reply_markup=back_home_kb())
        return
    from app.keyboards import orders_list_kb
    await c.message.edit_text("📦 سفارشات من (۵ مورد اخیر):", reply_markup=orders_list_kb(rows))

@router.callback_query(F.data.startswith("order:detail:"))
async def order_detail(c: CallbackQuery):
    oid = int(c.data.split(":")[2])
    row = await fetchone("""SELECT o.id, o.tracking_code, o.status, p.title as plan_title, p.price, p.description, pr.title as product_title
                              FROM orders o 
                              JOIN plans p ON p.id=o.plan_id 
                              JOIN products pr ON pr.id=o.product_id
                              WHERE o.id=?""", oid)
    if not row:
        await c.answer("یافت نشد.", show_alert=True)
        return
    desc = (row['description'] or '').strip()
    txt = (f"جزئیات سفارش #{row['id']}\n"
           f"کد پیگیری: {row['tracking_code']}\n"
           f"محصول: {row['product_title']}\n"
           f"پلن: {row['plan_title']}\n"
           f"توضیح پلن: {desc if desc else '—'}\n"
           f"قیمت: {row['price']:,} تومان\n"
           f"وضعیت: {row['status']}")
    await c.message.edit_text(txt, reply_markup=back_home_kb())
