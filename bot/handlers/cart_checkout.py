from aiogram import Router, F
from aiogram.types import CallbackQuery
from common.db import SessionLocal
from common.models import Product, Order
from common.utils import format_price

router = Router()

@router.callback_query(F.data.startswith('buy:'))
async def buy(cq: CallbackQuery):
    pid = int(cq.data.split(':', 1)[1])
    with SessionLocal() as s:
        p = s.get(Product, pid)
        if not p:
            await cq.answer('محصول موجود نیست', show_alert=True)
            return
        o = Order(user_tg_id=cq.from_user.id, product_id=p.id, amount=p.price, currency=p.currency, status='pending_payment')
        s.add(o)
        s.commit()
    text = (f"سفارش ثبت شد: {p.name}\n"
            f"مبلغ: {format_price(p.price, p.currency)}\n\n"
            "برای تکمیل، پرداخت را انجام دهید و رسید را ارسال کنید.")
    await cq.message.edit_text(text)
