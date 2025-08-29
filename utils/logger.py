import logging
from config import ADMIN_IDS, ADMIN_ALERT_CHAT_ID

def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

async def report_error_to_admins(bot, text: str):
    targets = []
    if ADMIN_ALERT_CHAT_ID:
        targets.append(ADMIN_ALERT_CHAT_ID)
    elif ADMIN_IDS:
        targets.extend(ADMIN_IDS)
    for chat_id in targets:
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            pass
