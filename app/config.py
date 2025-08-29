# -*- coding: utf-8 -*-
import os

class Settings:
    def __init__(self):
        self.bot_token: str = os.getenv("BOT_TOKEN", "").strip()
        # لیست ادمین‌ها به صورت comma-separated
        admins_env = os.getenv("ADMINS", "").strip()
        if admins_env:
            try:
                self.admins = [int(x) for x in admins_env.split(",") if x.strip()]
            except Exception:
                self.admins = []
        else:
            self.admins = []
        # مسیر دیتابیس
        self.db_path: str = os.getenv("DB_PATH", "data/noxbot.sqlite3")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

settings = Settings()
