from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda message: message.text == "💄 Послуги")
async def services(message: Message):
    await message.answer(
        "💄 Наші послуги:\n\n"
        "• Перманент брів\n"
        "• Перманент губ\n"
        "• Перманент повік"
    )