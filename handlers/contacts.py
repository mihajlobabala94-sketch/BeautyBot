from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda message: message.text == "☎️ Контакти")
async def contacts(message: Message):
    await message.answer(
        "☎️ Телефон:\n+380992058456\n\n"
    )


@router.message(lambda message: message.text == "📍 вулиця Олександра Довженка, 25Б, Івано-Франківськ, Івано-Франківська область, 76000 ")
async def address(message: Message):
    await message.answer(
        "📍 м. Івано-Франківськ\n"
        "вул. Олександра Довженка, 25Б\n"
    )