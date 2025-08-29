# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ری‌اکشن‌ها (fallback اگر در aiogram موجود نباشد)
try:
    from aiogram.types import ReactionTypeEmoji
except Exception:
    ReactionTypeEmoji = None

from app.db import fetchone, fetchall, execute, get_setting
from app.keyboards import proof_kb

router = Router()

class ProofStates(StatesGroup):
    waiting = State()

def _gen_tracking():
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def _get_or_create_user_id(tg_user) -> int:
    row = await fetchone("SELECT id FROM users WHERE tg_id=?", tg_user.id)
    if row:
        return int(row["id"]) if isinstance(row, dict) else int(row[0])
    uid = await execute(
        "INSERT INTO users(tg_id, first_name, username) VALUES(?,?,?)",
        tg_user.id, tg_user.first_name or "", tg_user.username or ""
    )
    return uid

def _normalize_chat_id(chat: str | None) -> str | None:
    if not chat:
        return None
    s = chat.strip()
    if s.startswith("https://t.me/"):
        uname = s.split("/")[-1]
        s = "@" + uname
    if s.startswith("@") or s.lstrip("-").isdigit():
        return s
    return "@" + s

async def _notify_new_order(bot, order_id: int):
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

    dest_raw = await get_setting("ORDER_CHANNEL", None)
    dest = _normalize_chat_id(dest_raw)

    txt = f"""📥 سفارش جدید #{row['id']}
#️⃣ کد پیگیری: {row['tracking_code']}
👤 کاربر: <a href='tg://user?id={row['tg_id']}'>{row['first_name'] or 'کاربر'}</a>
🔖 یوزرنیم: @{row['username'] or '-'}
🆔 آیدی عددی: {row['tg_id']}
📦 محصول: {row['product_title']}
💠 پلن: {row['plan_title']}
💵 قیمت: {row['price']:,} تومان"""
    ok = False
    if dest:
        try:
            await bot.send_message(dest, txt, parse_mode="HTML")
            ok = True
        except Exception:
            ok = False

    # نوتیف دایرکت برای ادمین‌ها
    try:
        from app.config import settings
        admins = set(map(int, (settings.admins or "").split(","))) if isinstance(settings.admins, str) else set(settings.admins or [])
        for aid in admins:
            try:
                await bot.send_message(aid, f"🔔 سفارش جدید ثبت شد. کد پیگیری: {row['tracking_code']} (#{row['id']})")
            except Exception:
                pass
    except Exception:
        pass

    return ok

@router.callback_query(F.data.regexp(r"^pay:(\d+)$"))
async def pay_cb(c: CallbackQuery, state: FSMContext):
    plan_id = int(c.data.split(":")[1])
    plan = await fetchone(
        """SELECT p.id as plan_id, p.title as plan_title, p.price,
                  pr.title as product_title, pr.id as product_id
           FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?""",
        plan_id
    )
    if not plan:
        await c.answer("نامعتبر", show_alert=True)
        return

    user_id = await _get_or_create_user_id(c.from_user)
    trk = _gen_tracking()
    order_id = await execute(
        "INSERT INTO orders(user_id, product_id, plan_id, status, tracking_code) VALUES(?,?,?,?,?)",
        user_id, plan["product_id"], plan_id, "awaiting_proof", trk
    )

    # اطلاع کانال/ادمین‌ها
    await _notify_new_order(c.bot, order_id)

    # کارت
    card = await get_setting("card_number", "") or "—"
    info = f"""🔖 کد پیگیری: <b>{trk}</b>

لطفاً پس از واریز، با دکمه «🧾 ارسال رسید» عکس/فایل رسید را بفرستید.
مبلغ: {plan['price']:,} تومان
شماره کارت: {card}"""

    sent = await c.message.edit_text(info, reply_markup=proof_kb(order_id), parse_mode="HTML")

    # ری‌اکشن قلب ❤️ روی پیام
    if ReactionTypeEmoji:
        try:
            await c.bot.set_message_reaction(
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                reaction=[ReactionTypeEmoji(emoji="❤️")],
                is_big=True
            )
        except Exception:
            pass

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
    order_id = int(data.get("order_id"))
    file_id = m.photo[-1].file_id
    await execute("UPDATE orders SET proof_type=?, proof_value=?, status='awaiting_review' WHERE id=?",
                  "photo", file_id, order_id)
    await _send_proof_to_channel(m, order_id, "photo", file_id)
    await state.clear()
    sent = await m.answer("✅ رسید شما دریافت شد. پس از بررسی به شما اطلاع می‌دهیم.")
    if ReactionTypeEmoji:
        try:
            await m.bot.set_message_reaction(
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                reaction=[ReactionTypeEmoji(emoji="✅")],
                is_big=True
            )
        except Exception:
            pass

@router.message(ProofStates.waiting, F.document)
async def proof_document(m: Message, state: FSMContext):
    data = await state.get_data()
    order_id = int(data.get("order_id"))
    file_id = m.document.file_id
    await execute("UPDATE orders SET proof_type=?, proof_value=?, status='awaiting_review' WHERE id=?",
                  "document", file_id, order_id)
    await _send_proof_to_channel(m, order_id, "document", file_id)
    await state.clear()
    sent = await m.answer("✅ رسید شما دریافت شد. پس از بررسی به شما اطلاع می‌دهیم.")
    if ReactionTypeEmoji:
        try:
            await m.bot.set_message_reaction(
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                reaction=[ReactionTypeEmoji(emoji="✅")],
                is_big=True
            )
        except Exception:
            pass

@router.message(ProofStates.waiting)
async def proof_wrong(m: Message, state: FSMContext):
    await m.answer("لطفاً فقط عکس یا فایلِ رسید را ارسال کنید.")

async def _send_proof_to_channel(m: Message, order_id: int, kind: str, file_id: str):
    dest_raw = await get_setting("ORDER_CHANNEL", None)
    dest = _normalize_chat_id(dest_raw)
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
    caption = f"""🧾 رسید پرداخت برای سفارش #{row['id']}
#️⃣ کد پیگیری: {row['tracking_code']}
👤 کاربر: <a href='tg://user?id={row['tg_id']}'>{row['first_name'] or 'کاربر'}</a>
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
