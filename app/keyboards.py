from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .texts import *

def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MENU_STORE)],
                  [KeyboardButton(text=MENU_ACCOUNT), KeyboardButton(text=MENU_SUPPORT)],
                  [KeyboardButton(text=MENU_CHANNEL)]],
        resize_keyboard=True
    )
    return kb

def categories_kb(cats):
    builder = InlineKeyboardBuilder()
    for c in cats:
        builder.button(text=f"{c.title} (#{c.id})", callback_data=f"cat:{c.id}")
    return builder.as_markup()

def products_kb(products):
    builder = InlineKeyboardBuilder()
    for p in products:
        status = "✅" if p.is_active else "⛔"
        builder.button(text=f"{status} {p.title} (#{p.id})", callback_data=f"prod:{p.id}")
    return builder.as_markup()

def plans_kb(plans):
    builder = InlineKeyboardBuilder()
    for pl in plans:
        builder.button(text=f"{pl.title} - {int(pl.price)} تومان", callback_data=f"plan:{pl.id}")
    return builder.as_markup()

def payment_methods_kb(has_zp: bool, has_idpay: bool):
    builder = InlineKeyboardBuilder()
    builder.button(text=PAY_CARD_TO_CARD, callback_data="pay:c2c")
    if has_zp:
        builder.button(text=PAY_ZARINPAL, callback_data="pay:zarinpal")
    if has_idpay:
        builder.button(text=PAY_IDPAY, callback_data="pay:idpay")
    builder.adjust(1)
    return builder.as_markup()

def admin_panel_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_MANAGE_CATS), KeyboardButton(text=ADMIN_MANAGE_PRODUCTS)],
            [KeyboardButton(text=ADMIN_MANAGE_ORDERS)],
            [KeyboardButton(text=ADMIN_SETTINGS)],
            [KeyboardButton(text=ADMIN_BACK)]
        ],
        resize_keyboard=True
    )
    return kb

def admin_settings_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text=ADMIN_SET_SUPPORT, callback_data="set:support")
    builder.button(text=ADMIN_SET_CHANNEL, callback_data="set:channel")
    builder.button(text=ADMIN_SET_CARD, callback_data="set:card")
    builder.button(text=ADMIN_SET_ZARINPAL, callback_data="set:zp")
    builder.button(text=ADMIN_SET_IDPAY, callback_data="set:idpay")
    builder.adjust(1)
    return builder.as_markup()


def orders_actions_kb(oid: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=ORDER_APPROVE, callback_data=f"order:approve:{oid}")
    builder.button(text=ORDER_REJECT, callback_data=f"order:reject:{oid}")
    builder.adjust(2)
    return builder.as_markup()
