from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    BOT_TOKEN: str = "CHANGE_ME"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/botdb"
    REDIS_URL: str = "redis://cache:6379/0"
    ADMIN_SECRET: str = "change-me"
    ADMIN_ALLOWED_IDS: str = ""
    CURRENCY: str = "IRR"
    TZ: str = "Asia/Tehran"
    WEB_BASE_URL: str = "http://localhost:8080"
    BOT_WEBHOOK_SECRET: str = "change-me"

    class Config:
        env_file = ".env"
        case_sensitive = False
