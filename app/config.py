# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMINS: List[int] = Field(default_factory=list)
    BASE_URL: str = "http://localhost:8000"
    WEBHOOK_SECRET: str = "change-me"
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"
    SUPPORT_USERNAME: str | None = None
    CHANNEL_USERNAME: str | None = None
    CARD_NUMBER: str | None = None
    ZARINPAL_MERCHANT_ID: str | None = None
    ZARINPAL_SANDBOX: bool = True
    IDPAY_API_KEY: str | None = None
    IDPAY_SANDBOX: bool = True

    @field_validator("ADMINS", mode="before")
    @classmethod
    def parse_admins(cls, v):
        if isinstance(v, list): return [int(x) for x in v]
        if isinstance(v, int):  return [v]
        if isinstance(v, str):
            s = v.strip()
            if not s: return []
            if s.startswith("["):
                import json; return [int(x) for x in json.loads(s)]
            return [int(x) for x in s.split(",")]
        return v

    class Config:
        env_file = ".env"

settings = Settings()
