# common/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
try:
    # برای پشتیبانی از نام‌های متفاوت در env (حروف کوچک/بزرگ)
    from pydantic import AliasChoices
    ALIAS_USERNAME = AliasChoices("ADMIN_USERNAME", "admin_username")
    ALIAS_PASSWORD = AliasChoices("ADMIN_PASSWORD", "admin_password")
except Exception:
    # اگر نسخه پایدانتیک AliasChoices نداشت، با نام‌های اصلی کار می‌کنیم
    ALIAS_USERNAME = "ADMIN_USERNAME"
    ALIAS_PASSWORD = "ADMIN_PASSWORD"

class Settings(BaseSettings):
    # پیکربندی برای خواندن از .env، حساس نبودن به کوچکی/بزرگی حروف، و نادیده گرفتن کلیدهای اضافه
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    APP_ENV: str = "dev"
    BOT_TOKEN: str = "CHANGE_ME"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/botdb"
    REDIS_URL: str = "redis://cache:6379/0"

    # ورود پنل ادمین
    ADMIN_USERNAME: str = Field(default="admin", validation_alias=ALIAS_USERNAME)
    ADMIN_PASSWORD: str = Field(default="change-me", validation_alias=ALIAS_PASSWORD)
    ADMIN_SECRET: str = "change-me"   # برای امضای سشن کوکی

    ADMIN_ALLOWED_IDS: str = ""
    CURRENCY: str = "IRR"
    TZ: str = "Asia/Tehran"
    WEB_BASE_URL: str = "http://localhost:8080"
    BOT_WEBHOOK_SECRET: str = "change-me"
