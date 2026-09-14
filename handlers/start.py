from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.menu import main_menu

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Вітаємо!\n\n"
        "Я бот для запису до майстра перманентного макіяжу.\n\n"
        "Оберіть потрібний пункт нижче 👇",
        reply_markup=main_menu
    )