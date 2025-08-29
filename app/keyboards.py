# -*- coding: utf-8 -*-
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ===== User menus =====
def main_menu(
    is_admin: bool = False,
    channel_url: str | None = None,
    support_url: str | None = None
):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ فروشگاه", callback_data="shop")
    kb.button(text="📦 سفارشات من", callback_data="orders_me")
    kb.button(text="👤 حساب کاربری", callback_data="account")

    # فقط وقتی لینک‌ها تنظیم شده باشند نشان بده
    if channel_url:
        kb.button(text="📣 کانال ما", url=channel_url)
    if support_url:
        kb.button(text="🆘 پشتیبانی", url=support_url)

    if is_admin:
        kb.button(text="🛠️ پنل مدیریت", callback_data="admin:menu")

    # ردیف‌بندی
    if channel_url or support_url:
        kb.adjust(2, 2, 1, 1)  # با لینک‌ها
    else:
        kb.adjust(2, 1, 1)     # بدون لینک‌ها
    return kb.as_markup()

def back_home_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 منوی اصلی", callback_data="home")
    return kb.as_markup()

def shop_products_kb(prods):
    kb = InlineKeyboardBuilder()
    for p in prods:
        kb.button(text=f"🛒 {p['title']}", callback_data=f"product:{p['id']}")
    kb.button(text="🏠 منوی اصلی", callback_data="home")
    kb.adjust(1, 1)
    return kb.as_markup()

def shop_plans_kb(plans, product_id: int):
    kb = InlineKeyboardBuilder()
    for pl in plans:
        kb.button(text=f"💠 {pl['title']} | {pl['price']:,} تومان", callback_data=f"plan:{pl['id']}")
    kb.button(text="⬅️ محصولات", callback_data="shop")
    kb.adjust(1, 1)
    return kb.as_markup()

def pay_kb(plan_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 پرداخت کارت به کارت", callback_data=f"pay:{plan_id}")
    kb.button(text="⬅️ بازگشت", callback_data="shop")
    kb.adjust(1, 1)
    return kb.as_markup()

def proof_kb(order_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🧾 ارسال رسید", callback_data=f"proof:{order_id}")
    kb.button(text="❌ انصراف", callback_data="home")
    kb.adjust(1, 1)
    return kb.as_markup()

# ===== Admin menus =====
def admin_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 محصولات", callback_data="admin:prods")
    kb.button(text="💠 پلن‌ها", callback_data="admin:plans")
    kb.button(text="🧾 سفارش‌ها", callback_data="admin:orders")
    kb.button(text="⚙️ تنظیمات", callback_data="admin:settings")
    kb.button(text="🔎 جستجو با کد پیگیری", callback_data="admin:find_by_trk")
    kb.button(text="✨ افکت‌ها", callback_data="admin:effects")
    kb.button(text="📨 پیام همگانی", callback_data="admin:broadcast_copy")
    kb.button(text="🔁 فوروارد همگانی", callback_data="admin:broadcast_forward")
    kb.button(text="⬅️ منوی اصلی", callback_data="home")
    kb.adjust(2, 2, 2, 2, 1)
    return kb.as_markup()

def admin_effects_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="❤️ افکت ثبت سفارش", callback_data="admin:set_effect:CREATED")
    kb.button(text="🎉 افکت اتمام سفارش", callback_data="admin:set_effect:COMPLETED")
    kb.button(text="👎 افکت رد سفارش", callback_data="admin:set_effect:REJECTED")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def admin_settings_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 کانال اصلی", callback_data="admin:set:MAIN_CHANNEL")
    kb.button(text="📝 کانال سفارش‌ها", callback_data="admin:set:ORDER_CHANNEL")
    kb.button(text="📝 یوزرنیم پشتیبانی", callback_data="admin:set:SUPPORT_USERNAME")
    kb.button(text="📝 شماره کارت", callback_data="admin:set:CARD")
    kb.button(text="📝 متن خوش‌آمد", callback_data="admin:set:WELCOME_TEXT")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()

def admin_prods_kb(prods):
    kb = InlineKeyboardBuilder()
    for p in prods:
        kb.button(text=f"🧩 {p['title']}", callback_data=f"admin:edit_prod:{p['id']}")
        kb.button(text=f"📝 توضیح", callback_data=f"admin:prod_desc:{p['id']}")
        kb.button(text=f"💠 پلن‌ها", callback_data=f"admin:plans_for_prod:{p['id']}")
        kb.button(text=f"❌ حذف", callback_data=f"admin:del_prod:{p['id']}")
    kb.button(text="➕ افزودن محصول", callback_data="admin:add_prod")
    kb.button(text="⬅️ بازگشت", callback_data="admin:menu")
    kb.adjust(4, 1, 1)
    return kb.as_markup()

def admin_plans_list_kb(plans, pid: int):
    kb = InlineKeyboardBuilder()
    for pl in plans:
        kb.button(text=f"💰 قیمت «{pl['title']}»", callback_data=f"admin:edit_plan_price:{pl['id']}")
        kb.button(text=f"✏️ عنوان", callback_data=f"admin:edit_plan:{pl['id']}")
        kb.button(text=f"❌ حذف", callback_data=f"admin:del_plan:{pl['id']}")
    kb.button(text="➕ افزودن پلن", callback_data=f"admin:add_plan:{pid}")
    kb.button(text="⬅️ محصولات", callback_data="admin:prods")
    kb.adjust(3, 1, 1)
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
    kb.adjust(2, 2)
    return kb.as_markup()
