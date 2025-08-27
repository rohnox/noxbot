from dataclasses import dataclass

@dataclass
class PaymentLink:
    url: str
    authority: str | None = None

class PaymentGatewayBase:
    async def create_payment(self, amount: int, description: str, callback_url: str) -> PaymentLink:
        raise NotImplementedError

    async def verify_payment(self, *args, **kwargs):
        raise NotImplementedError
