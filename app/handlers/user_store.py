# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.db import fetchone, fetchall, execute, get_setting
from app.keyboards import pay_kb, proof_kb

router = Router()

class ProofStates(StatesGroup):
    waiting = State()

def _gen_tracking():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def _get_or_create_user_id(tg_user) -> int:
    row = await fetchone("SELECT id FROM users WHERE tg_id=?", tg_user.id)
    if row:
        return int(row["id"])
    uid = await execute(
        "INSERT INTO users(tg_id, first_name, username) VALUES(?,?,?)",
        tg_user.id, tg_user.first_name or "", tg_user.username or ""
    )
    return uid

async def _notify_new_order(bot, order_id: int):
    # سفارش را بخوان برای توضیح
    row = await fetchone(
        """SELECT o.id, o.tracking_code, p.title as plan_title, pr.title as product_title, p.price,
                  u.tg_id, u.username, u.first_name
           FROM orders o
           JOIN plans p ON p.id=o.plan_id
           JOIN products pr ON pr.id=p.product_id
           JOIN users u ON u.id=o.user_id
           WHERE o.id=?""",
        order_id
    )
    if not row:
        return False
    dest = await get_setting("ORDER_CHANNEL", None)
    if not dest:
        return False

    mention = f"<a href='tg://user?id={row['tg_id']}'>{row['first_name'] or 'کاربر'}</a>"
    txt = f"""📥 سفارش جدید #{row['id']}
#️⃣ کد پیگیری: {row['tracking_code']}
👤 کاربر: {mention}
🔖 یوزرنیم: @{row['username'] or '-'}
🆔 آیدی عددی: {row['tg_id']}
📦 محصول: {row['product_title']}
💠 پلن: {row['plan_title']}
💵 قیمت: {row['price']:,} تومان"""

    try:
        await bot.send_message(dest, txt, parse_mode="HTML")
        return True
    except Exception:
        return False

    mention = f"<a href='tg://user?id={row['tg_id']}'>{row['first_name'] or 'کاربر'}</a>"
    txt = f"""📥 سفارش جدید #{row['id']}
کد پیگیری: {row['tracking_code']}
کاربر: {mention} @{row['username'] or '-'}
محصول: {row['product_title']}
پلن: {row['plan_title']}
قیمت: {row['price']:,} تومان"""
    try:
        await bot.send_message(dest, txt, parse_mode="HTML")
        return True
    except Exception:
        return False

@router.callback_query(F.data.regexp(r"^pay:(\d+)$"))
async def pay_cb(c: CallbackQuery, state: FSMContext):
    plan_id = int(c.data.split(":")[1])
    plan = await fetchone(
        """SELECT p.id as plan_id, p.title as plan_title, p.price, p.description,
                  pr.title as product_title, pr.id as product_id
           FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?""",
        plan_id
    )
    if not plan:
        await c.answer("نامعتبر", show_alert=True)
        return

    # کارت
    card = await get_setting("card_number", "") or "—"

    info = f"""🔖 اطلاعات پرداخت
محصول: {plan['product_title']}
پلن: {plan['plan_title']}
مبلغ: {plan['price']:,} تومان
شماره کارت: {card}

پس از واریز، با دکمه «🧾 ارسال رسید»، عکس/فایل رسید را ارسال کنید.
(تا قبل از ارسال رسید، سفارش ثبت نمی‌شود)"""

    await state.set_state(ProofStates.waiting)
    await state.update_data(plan_id=plan['plan_id'], product_id=plan['product_id'])
    try:
        await c.message.edit_text(info, reply_markup=proofnew_kb(plan['plan_id']), parse_mode="HTML")
    except Exception:
        await c.message.answer(info, reply_markup=proofnew_kb(plan['plan_id']), parse_mode="HTML")

# === Proof (رسید پرداخت) ===
@router.callback_query(F.data.regexp(r"^proof:(\d+)$"))
async def proof_start(c: CallbackQuery, state: FSMContext):
    order_id = int(c.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(ProofStates.waiting)
    await c.message.answer("🧾 لطفاً عکسِ رسید یا فایلِ رسید را ارسال کنید.\n(برای لغو: منوی اصلی)")

@router.message(ProofStates.waiting, F.photo)
async def proof_photo(m: Message, state: FSMContext):
    data = await state.get_data()
    plan_id = data.get("plan_id")
    product_id = data.get("product_id")
    file_id = m.photo[-1].file_id

    if plan_id and product_id:
        # Create order now (first time)
        user_id = await _get_or_create_user_id(m.from_user)
        trk = _gen_tracking()
        order_id = await execute(
            "INSERT INTO orders(user_id, product_id, plan_id, status, proof_type, proof_value, tracking_code) VALUES(?,?,?,?,?,?,?)",
            user_id, int(product_id), int(plan_id), "awaiting_review", "photo", file_id, trk
        )
        await _send_proof_to_channel(m, order_id, "photo", file_id)
        await state.clear()
    else:
        # Backward compatibility (had order_id in state)
        order_id = int(data.get("order_id"))
        await execute("UPDATE orders SET proof_type=?, proof_value=?, status='awaiting_review' WHERE id=?", "photo", file_id, order_id)
        await _send_proof_to_channel(m, order_id, "photo", file_id)
        await state.clear()

    await m.answer("✅ رسید شما دریافت شد. پس از بررسی به شما اطلاع می‌دهیم.")
    try:
        await react_emoji(m.bot, m.chat.id, m.message_id, "❤️", big=True)
    except Exception:
        pass

    # نمایش منوی اصلی
    from app.config import is_admin
    from app.keyboards import main_menu
    kb = main_menu(is_admin(m.from_user.id))
    await m.answer("منوی اصلی:", reply_markup=kb)

@router.message(ProofStates.waiting, F.document)
async def proof_document(m: Message, state: FSMContext):
    data = await state.get_data()
    plan_id = data.get("plan_id")
    product_id = data.get("product_id")
    file_id = m.document.file_id

    if plan_id and product_id:
        user_id = await _get_or_create_user_id(m.from_user)
        trk = _gen_tracking()
        order_id = await execute(
            "INSERT INTO orders(user_id, product_id, plan_id, status, proof_type, proof_value, tracking_code) VALUES(?,?,?,?,?,?,?)",
            user_id, int(product_id), int(plan_id), "awaiting_review", "document", file_id, trk
        )
        await _send_proof_to_channel(m, order_id, "document", file_id)
        await state.clear()
    else:
        order_id = int(data.get("order_id"))
        await execute("UPDATE orders SET proof_type=?, proof_value=?, status='awaiting_review' WHERE id=?", "document", file_id, order_id)
        await _send_proof_to_channel(m, order_id, "document", file_id)
        await state.clear()

    await m.answer("✅ رسید شما دریافت شد. پس از بررسی به شما اطلاع می‌دهیم.")
    try:
        await react_emoji(m.bot, m.chat.id, m.message_id, "❤️", big=True)
    except Exception:
        pass

    from app.config import is_admin
    from app.keyboards import main_menu
    kb = main_menu(is_admin(m.from_user.id))
    await m.answer("منوی اصلی:", reply_markup=kb)
@router.message(ProofStates.waiting)
async def proof_wrong(m: Message, state: FSMContext):
    await m.answer("لطفاً فقط عکس یا فایلِ رسید را ارسال کنید.")

async def _send_proof_to_channel(m: Message, order_id: int, kind: str, file_id: str):
    dest = await get_setting("ORDER_CHANNEL", None)
    if not dest:
        return
    row = await fetchone(
        """SELECT o.id, o.tracking_code, p.title as plan_title, pr.title as product_title, p.price,
                  u.tg_id, u.username, u.first_name
           FROM orders o
           JOIN plans p ON p.id=o.plan_id
           JOIN products pr ON pr.id=p.product_id
           JOIN users u ON u.id=o.user_id
           WHERE o.id=?""",
        order_id
    )
    if not row:
        return
    mention = f"<a href='tg://user?id={row['tg_id']}'>{row['first_name'] or 'کاربر'}</a>"
    caption = f"""🧾 رسید پرداخت برای سفارش #{row['id']}
#️⃣ کد پیگیری: {row['tracking_code']}
👤 کاربر: {mention}
🔖 یوزرنیم: @{row['username'] or '-'}
🆔 آیدی عددی: {row['tg_id']}
📦 محصول: {row['product_title']}
💠 پلن: {row['plan_title']}
💵 قیمت: {row['price']:,} تومان"""
    try:
        if kind == "photo":
            await m.bot.send_photo(dest, photo=file_id, caption=caption, parse_mode="HTML")
        else:
            await m.bot.send_document(dest, document=file_id, caption=caption, parse_mode="HTML")
    except Exception:
        pass


@router.callback_query(F.data.regexp(r"^proofnew:(\d+)$"))
async def proof_new(c: CallbackQuery, state: FSMContext):
    plan_id = int(c.data.split(":")[1])
    # Ensure state has plan_id/product_id
    plan = await fetchone("SELECT id as plan_id, product_id FROM plans WHERE id=?", plan_id)
    if not plan:
        await c.answer("پلن نامعتبر است.", show_alert=True); return
    await state.set_state(ProofStates.waiting)
    await state.update_data(plan_id=plan['plan_id'], product_id=plan['product_id'])
    await c.message.answer("🧾 رسید پرداخت را به‌صورت عکس یا فایل بفرستید.")
