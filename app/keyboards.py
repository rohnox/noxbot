# -*- coding: utf-8 -*-
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu(is_admin: bool = False):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ فروشگاه", callback_data="shop")
    kb.button(text="📦 سفارشات من", callback_data="orders_me")
    kb.button(text="👤 حساب کاربری", callback_data="account")
    kb.button(text="📣 کانال ما", callback_data="channel")
    kb.button(text="🆘 پشتیبانی", callback_data="support")
    if is_admin:
        kb.button(text="🛠️ پنل مدیریت", callback_data="admin:menu")
    kb.adjust(2,2,1,1)
    return kb.as_markup()

def back_home_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 منوی اصلی", callback_data="home")
    return kb.as_markup()

def admin_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 محصولات", callback_data="admin:prods")
    kb.button(text="💠 پلن‌ها", callback_data="admin:plans")
    kb.button(text="🧾 سفارش‌ها", callback_data="admin:orders")
    kb.button(text="⚙️ تنظیمات", callback_data="admin:settings")
    kb.button(text="🔎 جستجو با کد پیگیری", callback_data="admin:find_by_trk")
    kb.button(text="📨 پیام همگانی", callback_data="admin:broadcast_copy")
    kb.button(text="🔁 فوروارد همگانی", callback_data="admin:broadcast_forward")
    kb.button(text="⬅️ منوی اصلی", callback_data="home")
    kb.adjust(2,2,2,1,1)
    return kb.as_markup()

def admin_prods_kb(prods):
    kb = InlineKeyboardBuilder()
    for p in prods:
        kb.button(text=f"🧩 {p['title']} ❌", callback_data=f"admin:del_prod:{p['id']}")
    kb.button(text="➕ افزودن محصول", callback_data="admin:add_prod")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()

def admin_plans_prod_kb(prods):
    kb = InlineKeyboardBuilder()
    for p in prods:
        kb.button(text=f"📦 {p['title']} ▶️ پلن‌ها", callback_data=f"admin:plans_for_prod:{p['id']}")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()

def admin_orders_kb(orders):
    kb = InlineKeyboardBuilder()
    for o in orders:
        kb.button(text=f"#{o['id']} | {o['status']}", callback_data=f"admin:order_view:{o['id']}")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()

def admin_order_actions_kb(order_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔧 در حال انجام", callback_data=f"admin:order_processing:{order_id}")
    kb.button(text="✅ اتمام کار", callback_data=f"admin:order_complete:{order_id}")
    kb.button(text="❌ رد", callback_data=f"admin:order_reject:{order_id}")
    kb.button(text="⬅️ لیست سفارش‌ها", callback_data="admin:orders")
    kb.adjust(2,2)
    return kb.as_markup()
