import httpx
from ..payments.base import PaymentGatewayBase, PaymentLink
from ...config import settings

IDPAY_BASE = "https://sandbox-api.idpay.ir/v1.1" if settings.IDPAY_SANDBOX else "https://api.idpay.ir/v1.1"

class IDPayGateway(PaymentGatewayBase):
    async def create_payment(self, amount: int, description: str, callback_url: str) -> PaymentLink:
        payload = {
            "order_id": "auto",  # می‌توانید شناسه اختصاصی بگذارید
            "amount": amount,
            "name": "Customer",
            "desc": description,
            "callback": callback_url,
        }
        headers = {
            "X-API-KEY": settings.IDPAY_API_KEY or "",
            "X-SANDBOX": "1" if settings.IDPAY_SANDBOX else "0",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{IDPAY_BASE}/payment", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            link = data["link"]
            return PaymentLink(url=link, authority=data.get("id"))

    async def verify_payment(self, idpay_id: str, order_id: str):
        payload = {"id": idpay_id, "order_id": order_id}
        headers = {
            "X-API-KEY": settings.IDPAY_API_KEY or "",
            "X-SANDBOX": "1" if settings.IDPAY_SANDBOX else "0",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{IDPAY_BASE}/payment/verify", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data  # status == 100 یا 101 یعنی موفق
