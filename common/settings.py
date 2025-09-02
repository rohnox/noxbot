# common/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
try:
    from pydantic import AliasChoices
    ALIAS_USERNAME = AliasChoices("ADMIN_USERNAME", "admin_username")
    ALIAS_PASSWORD = AliasChoices("ADMIN_PASSWORD", "admin_password")
except Exception:
    ALIAS_USERNAME = "ADMIN_USERNAME"
    ALIAS_PASSWORD = "ADMIN_PASSWORD"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",   # کلیدهای اضافه را نادیده بگیر
    )

    APP_ENV: str = "dev"
    BOT_TOKEN: str = "CHANGE_ME"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/botdb"
    REDIS_URL: str = "redis://cache:6379/0"

    # برای پنل ادمین
    ADMIN_USERNAME: str = Field(default="admin", validation_alias=ALIAS_USERNAME)
    ADMIN_PASSWORD: str = Field(default="change-me", validation_alias=ALIAS_PASSWORD)
    ADMIN_SECRET: str = "change-me"

    ADMIN_ALLOWED_IDS: str = ""
    CURRENCY: str = "IRR"
    TZ: str = "Asia/Tehran"
    WEB_BASE_URL: str = "http://localhost:8080"
    BOT_WEBHOOK_SECRET: str = "change-me"
