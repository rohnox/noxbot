from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import SessionLocal
from ..models import Order, OrderStatus, PaymentMethod
from ..services.payments.zarinpal import ZarinpalGateway
from ..services.payments.idpay import IDPayGateway

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("/zarinpal/callback")
async def zarinpal_callback(oid: int, Authority: str | None = None, Status: str | None = None):
    async with SessionLocal() as db:
        res = await db.execute(select(Order).where(Order.id==oid))
        order = res.scalar_one_or_none()
        if not order:
            raise HTTPException(404, "order not found")
        if Status != "OK" or not Authority:
            order.status = OrderStatus.failed
            await db.commit()
            return {"ok": False, "msg": "payment canceled"}
        gw = ZarinpalGateway()
        data = await gw.verify_payment(authority=Authority, amount=int(order.amount))
        if data.get("Status") == 100:
            order.status = OrderStatus.paid
            order.gateway_track_id = str(data.get("RefID"))
            await db.commit()
            return {"ok": True, "ref_id": order.gateway_track_id}
        else:
            order.status = OrderStatus.failed
            await db.commit()
            return {"ok": False, "data": data}

@router.post("/idpay/callback")
async def idpay_callback(request: Request):
    payload = await request.json()
    oid = int(request.query_params.get("oid", "0"))
    idpay_id = payload.get("id")
    order_id = payload.get("order_id", "auto")
    status = payload.get("status")
    # IDPay ابتدا با status 10 یا 100 برمی‌گردد؛ برای اطمینان verify لازم است.
    async with SessionLocal() as db:
        res = await db.execute(select(Order).where(Order.id==oid))
        order = res.scalar_one_or_none()
        if not order:
            raise HTTPException(404, "order not found")
        gw = IDPayGateway()
        data = await gw.verify_payment(idpay_id=idpay_id, order_id=order_id)
        if data.get("status") in (100, 101):
            order.status = OrderStatus.paid
            order.gateway_track_id = str(data.get("track_id"))
            await db.commit()
            return {"ok": True, "track_id": order.gateway_track_id}
        else:
            order.status = OrderStatus.failed
            await db.commit()
            return {"ok": False, "data": data}
