# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart

from app.db import fetchall, fetchone, get_setting, upsert_user
from app.keyboards import main_menu, back_home_kb, shop_products_kb, shop_plans_kb, pay_kb

router = Router()

def _build_urls(main_ch: str | None, sup: str | None):
    channel_url = None
    support_url = None
    if main_ch:
        s = main_ch.strip()
        if s.startswith("http"):
            channel_url = s
        elif s.startswith("@"):
            channel_url = f"https://t.me/{s[1:]}"
        elif s.startswith("-100") or s.lstrip("-").isdigit():
            channel_url = None  # آیدی خصوصی لینک‌پذیر نیست
    if sup:
        s = sup.strip()
        if not s.startswith("@"):
            s = "@" + s
        support_url = f"https://t.me/{s[1:]}"
    return channel_url, support_url

@router.message(CommandStart())
async def start_cmd(m: Message):
    await upsert_user(m.from_user.id, m.from_user.first_name or "", m.from_user.username or "", 0)

    from app.config import settings
    admins = set(map(int, (settings.admins or "").split(","))) if isinstance(settings.admins, str) else set(settings.admins or [])
    is_admin = m.from_user.id in admins

    main_ch = await get_setting("MAIN_CHANNEL", None)
    sup = await get_setting("SUPPORT_USERNAME", None)
    ch_url, sup_url = _build_urls(main_ch, sup)

    welcome = await get_setting("WELCOME_TEXT", "خوش آمدید 👋")
    await m.answer(welcome, reply_markup=main_menu(is_admin, ch_url, sup_url))

# بکاپ برای هر نوع /start متنی
@router.message(F.text.startswith("/start"))
async def start_cmd_text_fallback(m: Message):
    return await start_cmd(m)

@router.callback_query(F.data == "home")
async def go_home(cb: CallbackQuery):
    from app.config import settings
    admins = set(map(int, (settings.admins or "").split(","))) if isinstance(settings.admins, str) else set(settings.admins or [])
    is_admin = cb.from_user.id in admins

    main_ch = await get_setting("MAIN_CHANNEL", None)
    sup = await get_setting("SUPPORT_USERNAME", None)
    ch_url, sup_url = _build_urls(main_ch, sup)

    try:
        await cb.message.edit_text("منوی اصلی:", reply_markup=main_menu(is_admin, ch_url, sup_url))
    except TelegramBadRequest:
        await cb.message.answer("منوی اصلی:", reply_markup=main_menu(is_admin, ch_url, sup_url))

# ---- فروشگاه ----
@router.callback_query(F.data == "shop")
async def shop_menu(cb: CallbackQuery):
    prods = await fetchall("SELECT id, title FROM products ORDER BY id DESC")
    if not prods:
        try:
            await cb.message.edit_text("هیچ محصولی ثبت نشده.", reply_markup=back_home_kb())
        except TelegramBadRequest:
            await cb.message.answer("هیچ محصولی ثبت نشده.", reply_markup=back_home_kb())
        return
    txt = "🛍️ محصولات موجود:"
    try:
        await cb.message.edit_text(txt, reply_markup=shop_products_kb(prods))
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=shop_products_kb(prods))

@router.callback_query(F.data.startswith("product:"))
async def shop_product(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])

    prod = await fetchone("SELECT title FROM products WHERE id=?", pid)
    prod_title = prod["title"] if prod else f"#{pid}"
    desc = await get_setting(f"PROD_DESC_{pid}", None)

    plans = await fetchall("SELECT id, title, price FROM plans WHERE product_id=? ORDER BY price ASC", pid)

    base = f"🧾 محصول: {prod_title}"
    if desc:
        base += f"\n\n{desc}"

    if not plans:
        try:
            await cb.message.edit_text(base + "\n\nبرای این محصول پلنی تعریف نشده.", reply_markup=back_home_kb())
        except TelegramBadRequest:
            await cb.message.answer(base + "\n\nبرای این محصول پلنی تعریف نشده.", reply_markup=back_home_kb())
        return

    try:
        await cb.message.edit_text(base + "\n\n💠 پلن‌های موجود:", reply_markup=shop_plans_kb(plans, pid))
    except TelegramBadRequest:
        await cb.message.answer(base + "\n\n💠 پلن‌های موجود:", reply_markup=shop_plans_kb(plans, pid))

@router.callback_query(F.data.startswith("plan:"))
async def shop_plan(cb: CallbackQuery):
    plid = int(cb.data.split(":")[1])
    row = await fetchone(
        "SELECT p.title as plan_title, p.price, pr.title as product_title "
        "FROM plans p JOIN products pr ON pr.id=p.product_id WHERE p.id=?",
        plid,
    )
    if not row:
        await cb.answer("پلن یافت نشد.", show_alert=True)
        return
    txt = f"""🧾 جزئیات پلن:
محصول: {row['product_title']}
عنوان پلن: {row['plan_title']}
قیمت: {row['price']:,} تومان"""
    try:
        await cb.message.edit_text(txt, reply_markup=pay_kb(plid))
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=pay_kb(plid))

# ---- حساب کاربری ----
@router.callback_query(F.data == "account")
async def account_view(cb: CallbackQuery):
    u = cb.from_user
    txt = f"""👤 حساب کاربری
نام: {u.first_name or '-'}
یوزرنیم: @{u.username or '-'}
آیدی عددی: {u.id}"""
    try:
        await cb.message.edit_text(txt, reply_markup=back_home_kb())
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=back_home_kb())

# ---- سفارشات من ----
@router.callback_query(F.data == "orders_me")
async def orders_me(cb: CallbackQuery):
    row = await fetchone("SELECT id FROM users WHERE tg_id=?", cb.from_user.id)
    if not row:
        await cb.answer("هنوز سفارشی ندارید.", show_alert=True)
        return
    uid = int(row["id"]) if isinstance(row, dict) else int(row[0])
    orders = await fetchall(
        """SELECT o.id, o.tracking_code, o.status, o.created_at,
                  p.title as plan_title, pr.title as product_title
           FROM orders o
           JOIN plans p ON p.id=o.plan_id
           JOIN products pr ON pr.id=p.product_id
           WHERE o.user_id=? ORDER BY o.id DESC LIMIT 10""",
        uid
    )
    if not orders:
        msg = "🧾 هنوز سفارشی ثبت نکرده‌اید."
    else:
        lines = []
        for o in orders:
            ct = (o["created_at"] if isinstance(o, dict) else o[3]) or "-"
            lines.append(f"#{o['id']} | {o['status']} | {o['tracking_code'] or '—'} | {ct} | {o['product_title']} - {o['plan_title']}")
        msg = "🧾 سفارش‌های اخیر شما:\n" + "\n".join(lines)
    try:
        await cb.message.edit_text(msg, reply_markup=back_home_kb())
    except TelegramBadRequest:
        await cb.message.answer(msg, reply_markup=back_home_kb())
