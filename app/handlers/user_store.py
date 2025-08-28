# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.db import fetchone, execute, get_setting, get_or_create_user_id
from app.keyboards import pay_kb, proof_kb
from app import texts
from app.config import settings
from app.services.orders import notify_order

router = Router()

def _gen_tracking():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.callback_query(F.data.regexp(r"^pay:(\d+)$"))
async def pay_cb(c: CallbackQuery, state: FSMContext):
    plan_id = int(c.data.split(":")[1])
    plan = await fetchone("""SELECT p.id as plan_id, p.title as plan_title, p.price, p.description,
                                   pr.title as product_title, pr.id as product_id
                            FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?""", plan_id)
    if not plan:
        await c.answer("نامعتبر", show_alert=True)
        return

    tg_user_id = c.from_user.id
    user_id = await get_or_create_user_id(tg_user_id)
    trk = _gen_tracking()
    order_id = await execute("INSERT INTO orders(user_id, product_id, plan_id, status, tracking_code) VALUES(?,?,?,?,?)",
                             user_id, plan["product_id"], plan_id, "awaiting_proof", trk)

    mention = f"<a href='tg://user?id={c.from_user.id}'>{c.from_user.first_name or 'user'}</a>"
    try:
        ok = await notify_order(c.bot, order_id, mention, plan["product_title"], plan["plan_title"], int(plan["price"]), trk, c.from_user.id, c.from_user.username)
    except Exception:
        ok = False

    card = await get_setting("card_number", settings.card_number or "")
    card = card or "—"

    info = texts.TRACKING_ASSIGNED.format(trk=trk) + "\n\n" + texts.CARD_INFO.format(price=plan["price"], card=card)
    if not ok:
        info = "⚠️ اعلان به کانال سفارش‌ها ارسال نشد (دسترسی/تنظیمات را بررسی کنید).\n\n" + info

    await c.message.edit_text(info, reply_markup=proof_kb(order_id))
