# -*- coding: utf-8 -*-
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def main_menu(is_admin: bool, main_channel_url: str | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ فروشگاه", callback_data="store")
    if main_channel_url:
        kb.button(text="📣 کانال ما", url=main_channel_url)
    kb.button(text="👤 حساب", callback_data="account")
    kb.button(text="📦 سفارشات من", callback_data="orders:mine")
    kb.button(text="🆘 ارتباط با پشتیبانی", callback_data="support")
    if is_admin:
        kb.button(text="پنل مدیریت 🛠️", callback_data="admin:menu")
    kb.adjust(2, 2, 2)
    return kb.as_markup()

def back_home_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ بازگشت", callback_data="home")
    return kb.as_markup()

def categories_kb(items):
    kb = InlineKeyboardBuilder()
    for r in items:
        kb.button(text=f"📦 {r['title']}", callback_data=f"cat:{r['id']}")
    kb.button(text="⬅️ منوی اصلی", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()

def products_kb(items, __unused: int | None = None):
    kb = InlineKeyboardBuilder()
    for r in items:
        kb.button(text=f"🧩 {r['title']}", callback_data=f"prod:{r['id']}")
    kb.button(text="⬅️ دسته‌ها", callback_data="store")
    kb.adjust(1)
    return kb.as_markup()

def plans_kb(items, product_id: int):
    kb = InlineKeyboardBuilder()
    for r in items:
        kb.button(text=f"💠 {r['title']} - {r['price']:,} تومان", callback_data=f"plan:{r['id']}")
    kb.button(text="⬅️ محصولات", callback_data=f"back:products:{product_id}")
    kb.adjust(1)
    return kb.as_markup()

def pay_kb(plan_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="پرداخت کارت به کارت 💳", callback_data=f"pay:{plan_id}")
    kb.button(text="❌ لغو", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()

def proof_kb(order_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🧾 ارسال رسید", callback_data=f"proof:{order_id}")
    kb.button(text="⬅️ منوی اصلی", callback_data="home")
    kb.adjust(1)
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
        kb.button(text=f"🧩 {p['title']}", callback_data=f"admin:plans_prod:{p['id']}")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()

def admin_plans_kb(plans, prod_id:int):
    kb = InlineKeyboardBuilder()
    for pl in plans:
        kb.button(text=f"💠 {pl['title']} - {pl['price']:,} ❌", callback_data=f"admin:del_plan:{pl['id']}")
    kb.button(text="➕ افزودن پلن", callback_data=f"admin:add_plan:{prod_id}")
    kb.button(text="⬅️ انتخاب محصول", callback_data="admin:plans")
    kb.adjust(1)
    return kb.as_markup()

def admin_settings_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ خوش‌آمدگویی", callback_data="admin:set:welcome")
    kb.button(text="🆘 پشتیبانی", callback_data="admin:set:support")
    kb.button(text="💳 شماره کارت", callback_data="admin:set:card")
    kb.button(text="📣 کانال سفارش‌ها", callback_data="admin:set:channel")
    kb.button(text="📢 کانال اصلی", callback_data="admin:set:main_channel")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(2,2,2)
    return kb.as_markup()

def admin_orders_kb(orders):
    kb = InlineKeyboardBuilder()
    for o in orders:
        kb.button(text=f"#{o['id']} - {o['status']}", callback_data=f"admin:order:{o['id']}")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()

def admin_order_actions_kb(order_id:int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔧 در حال انجام", callback_data=f"admin:order_processing:{order_id}")
    kb.button(text="✅ اتمام کار", callback_data=f"admin:order_complete:{order_id}")
    kb.button(text="❌ رد", callback_data=f"admin:order_reject:{order_id}")
    kb.button(text="⬅️ بازگشت", callback_data="admin:orders")
    kb.adjust(2,1)
    return kb.as_markup()

def plan_summary_kb(plan_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ افزودن توضیح", callback_data=f"note:add:{plan_id}")
    kb.button(text="ادامه پرداخت 💳", callback_data=f"pay:{plan_id}")
    kb.button(text="❌ لغو", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()

def orders_list_kb(orders):
    kb = InlineKeyboardBuilder()
    for o in orders:
        kb.button(text=f"#{o['id']} | {o['tracking_code'] or '-'}", callback_data=f"order:detail:{o['id']}")
    kb.button(text="⬅️ منوی اصلی", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()
