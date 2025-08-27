import httpx
from ..payments.base import PaymentGatewayBase, PaymentLink
from ...config import settings

ZP_BASE = "https://sandbox.zarinpal.com/pg/rest/WebGate" if settings.ZARINPAL_SANDBOX else "https://api.zarinpal.com/pg/rest/WebGate"
ZP_START = "https://sandbox.zarinpal.com/pg/StartPay/" if settings.ZARINPAL_SANDBOX else "https://www.zarinpal.com/pg/StartPay/"

class ZarinpalGateway(PaymentGatewayBase):
    async def create_payment(self, amount: int, description: str, callback_url: str) -> PaymentLink:
        payload = {
            "MerchantID": settings.ZARINPAL_MERCHANT_ID,
            "Amount": amount,
            "Description": description,
            "CallbackURL": callback_url,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{ZP_BASE}/PaymentRequest.json", json=payload)
            r.raise_for_status()
            data = r.json()
            if data.get("Status") == 100:
                auth = data.get("Authority")
                return PaymentLink(url=f"{ZP_START}{auth}", authority=auth)
            else:
                raise RuntimeError(f"Zarinpal error: {data}")

    async def verify_payment(self, authority: str, amount: int):
        payload = {
            "MerchantID": settings.ZARINPAL_MERCHANT_ID,
            "Authority": authority,
            "Amount": amount,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{ZP_BASE}/PaymentVerification.json", json=payload)
            r.raise_for_status()
            data = r.json()
            return data  # {'Status': 100, 'RefID': ...} when success
