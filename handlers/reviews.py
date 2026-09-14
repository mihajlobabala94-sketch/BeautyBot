from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda message: message.text == "📸 Галерея")
async def gallery(message: Message):
    await message.answer(
        "📸 Фото робіт скоро будуть тут."
    )


@router.message(lambda message: message.text == "⭐ Відгуки")
async def reviews(message: Message):
    await message.answer(
        "⭐ Відгуки клієнтів скоро з'являться."
    )