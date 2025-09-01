from aiogram import Router, F
from aiogram.types import CallbackQuery
from common.db import SessionLocal
from common.models import Order

router = Router()

@router.callback_query(F.data == 'orders:list')
async def list_orders(cq: CallbackQuery):
    with SessionLocal() as s:
        rows = (s.query(Order)
                .filter(Order.user_tg_id == cq.from_user.id)
                .order_by(Order.id.desc())
                .limit(10).all())
    if not rows:
        await cq.message.edit_text('هنوز سفارشی ثبت نکردی.')
        return
    lines = ["آخرین سفارش‌ها:"]
    for o in rows:
        lines.append(f"#{o.id} — {o.amount} {o.currency} — {o.status}")
    await cq.message.edit_text("\n".join(lines))
