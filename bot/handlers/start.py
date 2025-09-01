from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from bot.keyboards import main_kb

router = Router()

@router.message(CommandStart())
async def start_cmd(msg: Message):
    text = ("سلام! خوش اومدی 🌟\n"
            "با این ربات می‌تونی پریمیوم یا استارز سفارش بدی.")
    await msg.answer(text, reply_markup=main_kb())
