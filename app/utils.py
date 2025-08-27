from aiogram.filters import BaseFilter
from aiogram.types import Message
from .config import settings
from .models import Setting
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user and message.from_user.id in settings.ADMINS

async def get_or_create_settings(db: AsyncSession) -> Setting:
    from .models import Setting
    res = await db.execute(select(Setting))
    s = res.scalar_one_or_none()
    if not s:
        s = Setting(
            support_username=settings.SUPPORT_USERNAME,
            channel_username=settings.CHANNEL_USERNAME,
            card_number=settings.CARD_NUMBER
        )
        db.add(s)
        await db.commit()
        await db.refresh(s)
    return s
