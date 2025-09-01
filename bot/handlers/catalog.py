from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from common.db import SessionLocal
from common.models import Product

router = Router()

@router.callback_query(F.data.startswith('cat:'))
async def open_category(cq: CallbackQuery):
    kind = cq.data.split(':', 1)[1]
    with SessionLocal() as s:
        products = s.query(Product).filter_by(kind=kind, is_active=True).all()
    kb = []
    for p in products:
        kb.append([InlineKeyboardButton(text=f"{p.name} — {p.price} {p.currency}", callback_data=f"buy:{p.id}")])
    kb.append([InlineKeyboardButton(text='⬅️ بازگشت', callback_data='home')])
    await cq.message.edit_text(f"انتخاب {('پریمیوم' if kind=='premium' else 'استارز')}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
