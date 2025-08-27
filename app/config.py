from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str
    ADMINS: List[int] = Field(default_factory=list)

    # URLs
    BASE_URL: str = "http://localhost:8000"
    WEBHOOK_SECRET: str = "change-me"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"

    # Defaults
    SUPPORT_USERNAME: str | None = None
    CHANNEL_USERNAME: str | None = None

    # Card to Card
    CARD_NUMBER: str | None = None

    # Zarinpal
    ZARINPAL_MERCHANT_ID: str | None = None
    ZARINPAL_SANDBOX: bool = True

    # IDPay
    IDPAY_API_KEY: str | None = None
    IDPAY_SANDBOX: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
