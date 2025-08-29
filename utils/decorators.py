import functools
from typing import Callable, Any, Coroutine
from telegram import Update
from telegram.ext import ContextTypes
from database import is_banned, get_lang
from locales.messages import t
from config import ADMIN_IDS

def admin_only(func: Callable[..., Coroutine[Any, Any, Any]]):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        uid = update.effective_user.id if update.effective_user else None
        if uid not in ADMIN_IDS:
            lang = get_lang(uid) if uid else "fa"
            await (update.effective_message or update.effective_chat).reply_text(t(lang, "only_admin"))
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def not_banned(func: Callable[..., Coroutine[Any, Any, Any]]):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        uid = update.effective_user.id if update.effective_user else None
        if uid and is_banned(uid):
            lang = get_lang(uid)
            await (update.effective_message or update.effective_chat).reply_text(t(lang, "banned"))
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
