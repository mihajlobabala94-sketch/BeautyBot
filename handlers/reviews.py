from aiogram import Router, F
from aiogram.types import Message

from keyboards.menu import main_menu

router = Router()


@router.message(F.text == "📸 Галерея")
async def gallery(message: Message):
    await message.answer(
        "📸 Фото робіт скоро будуть тут ✨",
        reply_markup=main_menu
    )


@router.message(F.text == "⭐ Відгуки")
async def reviews(message: Message):
    await message.answer(
        "⭐ Відгуки клієнтів скоро з'являться ✨",
        reply_markup=main_menu
    )