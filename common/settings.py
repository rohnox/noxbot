# common/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
try:
    from pydantic import AliasChoices
    ALIAS_USERNAME = AliasChoices("ADMIN_USERNAME", "admin_username")
    ALIAS_PASSWORD = AliasChoices("ADMIN_PASSWORD", "admin_password")
    ALIAS_GATE_TOKEN = AliasChoices("ADMIN_GATE_TOKEN", "admin_gate_token")
    ALIAS_GATE_PARAM = AliasChoices("ADMIN_GATE_PARAM", "admin_gate_param")
    ALIAS_DASHBOARD_PATH = AliasChoices("DASHBOARD_PATH", "dashboard_path")
except Exception:
    ALIAS_USERNAME = "ADMIN_USERNAME"
    ALIAS_PASSWORD = "ADMIN_PASSWORD"
    ALIAS_GATE_TOKEN = "ADMIN_GATE_TOKEN"
    ALIAS_GATE_PARAM = "ADMIN_GATE_PARAM"
    ALIAS_DASHBOARD_PATH = "DASHBOARD_PATH"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
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
    ADMIN_SECRET: str = "change-me"   # برای امضای کوکی سشن

    # گیت مخفی آدرس‌بار
    ADMIN_GATE_TOKEN: str = Field(default="", validation_alias=ALIAS_GATE_TOKEN)   # اگر خالی باشه، گیت غیرفعال است
    ADMIN_GATE_PARAM: str = Field(default="gate", validation_alias=ALIAS_GATE_PARAM)

    ADMIN_ALLOWED_IDS: str = ""
    CURRENCY: str = "IRR"
    TZ: str = "Asia/Tehran"
    WEB_BASE_URL: str = "http://localhost:8080"
    BOT_WEBHOOK_SECRET: str = "change-me"
    DASHBOARD_PATH: str = Field(default="/", validation_alias=ALIAS_DASHBOARD_PATH)
