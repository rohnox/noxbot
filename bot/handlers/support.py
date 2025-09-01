from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == 'support')
async def support_info(cq: CallbackQuery):
    await cq.message.edit_text('برای پشتیبانی، پیام بده: @your_support_username')
