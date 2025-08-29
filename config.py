import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required.")

# Admins
ADMIN_IDS = []
_raw = os.getenv("ADMIN_IDS", "").strip()
if _raw:
    for x in _raw.split(","):
        x = x.strip()
        if x.lstrip("-").isdigit():
            ADMIN_IDS.append(int(x))
ADMIN_ALERT_CHAT_ID = int(os.getenv("ADMIN_ALERT_CHAT_ID", "0")) if os.getenv("ADMIN_ALERT_CHAT_ID", "").strip() else None

# DB & Locale
DB_PATH = os.getenv("DB_PATH", "shop.db")
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "fa")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tehran")

# Payments
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "").strip()
CURRENCY = os.getenv("CURRENCY", "USD").upper()

# Webhook
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() in ("1", "true", "yes", "on")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "").strip()
LISTEN_ADDR = os.getenv("LISTEN_ADDR", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
