# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from app.db import fetchall, fetchone, set_setting, get_setting, upsert_user
from app.keyboards import main_menu, back_home_kb, shop_products_kb, shop_plans_kb, pay_kb

router = Router()

@router.message(F.text == "/start")
async def start_cmd(m: Message):
    # upsert user
    await upsert_user(m.from_user.id, m.from_user.first_name or "", m.from_user.username or "", 0)
    # show main menu
    from app.config import settings
    admins = set(map(int, (settings.admins or "").split(","))) if isinstance(settings.admins, str) else set(settings.admins or [])
    is_admin = m.from_user.id in admins
    await m.answer("خوش آمدید 👋", reply_markup=main_menu(is_admin))

@router.callback_query(F.data == "home")
async def go_home(cb: CallbackQuery):
    from app.config import settings
    admins = set(map(int, (settings.admins or "").split(","))) if isinstance(settings.admins, str) else set(settings.admins or [])
    is_admin = cb.from_user.id in admins
    try:
        await cb.message.edit_text("منوی اصلی:", reply_markup=main_menu(is_admin))
    except TelegramBadRequest:
        await cb.message.answer("منوی اصلی:", reply_markup=main_menu(is_admin))

# ---- Shop ----
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
    plans = await fetchall("SELECT id, title, price FROM plans WHERE product_id=? ORDER BY price ASC", pid)
    if not plans:
        try:
            await cb.message.edit_text("برای این محصول پلنی تعریف نشده.", reply_markup=back_home_kb())
        except TelegramBadRequest:
            await cb.message.answer("برای این محصول پلنی تعریف نشده.", reply_markup=back_home_kb())
        return
    try:
        await cb.message.edit_text("💠 پلن‌های موجود:", reply_markup=shop_plans_kb(plans, pid))
    except TelegramBadRequest:
        await cb.message.answer("💠 پلن‌های موجود:", reply_markup=shop_plans_kb(plans, pid))

@router.callback_query(F.data.startswith("plan:"))
async def shop_plan(cb: CallbackQuery):
    plid = int(cb.data.split(":")[1])
    row = await fetchone("...", plid)
    if not row:
        await cb.answer("پلن یافت نشد.", show_alert=True)
        return
    txt = f"""🧾 جزئیات پلن:
محصول: {row['product_title']}
عنوان: {row['plan_title']}
قیمت: {row['price']:,} تومان
—
{row['description']}"""
    try:
        await cb.message.edit_text(txt, reply_markup=pay_kb(plid))
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=pay_kb(plid))


# ---- Account / Orders ----
@router.callback_query(F.data == "account")
async def account_info(cb: CallbackQuery):
    u = cb.from_user
    txt = f"""👤 حساب کاربری
نام: {u.first_name or '-'}
یوزرنیم: @{u.username or '-'}
آیدی: {u.id}"""
    try:
        await cb.message.edit_text(txt, reply_markup=back_home_kb())
    except TelegramBadRequest:
        await cb.message.answer(txt, reply_markup=back_home_kb())


@router.callback_query(F.data == "orders_me")
async def my_orders(cb: CallbackQuery):
    rows = await fetchall("""SELECT o.id, o.tracking_code, o.status, p.title as plan_title, pr.title as product_title, p.price
                              FROM orders o
                              JOIN plans p ON p.id=o.plan_id
                              JOIN products pr ON pr.id=o.product_id
                              JOIN users u ON u.id=o.user_id
                              WHERE u.tg_id=?
                              ORDER BY o.id DESC LIMIT 10""", cb.from_user.id)
    if not rows:
        msg = "هنوز سفارشی ندارید."
    else:
        parts = []
        for r in rows:
            parts.append(f"#{r['id']} | {r['status']} | کد: {r['tracking_code'] or '—'}\n{r['product_title']} - {r['plan_title']} | {r['price']:,} تومان")
        msg = "🧾 سفارش‌های اخیر شما:
" + "\n\n".join(parts)
    try:
        await cb.message.edit_text(msg, reply_markup=back_home_kb())
    except TelegramBadRequest:
        await cb.message.answer(msg, reply_markup=back_home_kb())

# ---- Channel / Support ----
@router.callback_query(F.data == "channel")
async def show_channel(cb: CallbackQuery):
    url = await get_setting("MAIN_CHANNEL", None)
    if not url:
        await cb.answer("کانال اصلی تنظیم نشده.", show_alert=True); return
    await cb.message.answer(f"📣 کانال ما: {url}")

@router.callback_query(F.data == "support")
async def show_support(cb: CallbackQuery):
    sup = await get_setting("SUPPORT_USERNAME", None)
    if sup and not sup.startswith("@"): sup = "@" + sup
    await cb.message.answer(f"🆘 پشتیبانی: {sup or '@support'}")
