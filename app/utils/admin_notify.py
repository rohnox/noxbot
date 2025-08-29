# -*- coding: utf-8 -*-
from aiogram import Bot
from typing import List
import os

async def _parse_admins(env_value: str) -> List[int]:
    parts = [p.strip() for p in (env_value or "").split(",") if p.strip()]
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except Exception:
            pass
    return out

async def get_admin_ids() -> List[int]:
    env_admins = os.getenv("ADMINS", "")
    ids = await _parse_admins(env_admins)
    if ids:
        return ids
    try:
        from app.config import settings
        return await _parse_admins(getattr(settings, "admins", ""))
    except Exception:
        return []

async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in await get_admin_ids():
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception:
            pass
