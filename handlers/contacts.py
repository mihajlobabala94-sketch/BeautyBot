from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda message: message.text == "☎️ Контакти")
async def contacts(message: Message):
    await message.answer(
        "☎️ Телефон:\n+380XXXXXXXXX"
    )


@router.message(lambda message: message.text == "📍 Адреса")
async def address(message: Message):
    await message.answer(
        "📍 м. Івано-Франківськ\n"
        "вул. __________"
    )