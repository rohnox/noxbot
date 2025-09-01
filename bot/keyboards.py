from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⭐ خرید پریمیوم', callback_data='cat:premium')],
        [InlineKeyboardButton(text='✨ خرید استارز', callback_data='cat:stars')],
        [InlineKeyboardButton(text='📦 سفارش‌های من', callback_data='orders:list')],
        [InlineKeyboardButton(text='🆘 پشتیبانی', callback_data='support')],
    ])
