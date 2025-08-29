# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

def _parse_admins(val: str) -> List[int]:
    if not val:
        return []
    parts = [p.strip() for p in val.split(",") if p.strip()]
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            pass
    return out

@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "").strip()
    admins: List[int] = field(default_factory=lambda: _parse_admins(os.getenv("ADMINS", "")))
    order_channel: Optional[str] = os.getenv("ORDER_CHANNEL", "").strip() or None
    main_channel: Optional[str] = os.getenv("MAIN_CHANNEL", "").strip() or None
    welcome_text: str = os.getenv("WELCOME_TEXT", "سلام! به فروشگاه خوش اومدی ✨").strip()
    support_username: str = os.getenv("SUPPORT_USERNAME", "").strip()
    card_number: str = os.getenv("CARD_NUMBER", "").strip()

settings = Settings()

def is_admin(user_id: int) -> bool:
    return user_id in settings.admins
