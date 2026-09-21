from aiogram import Router, F
from aiogram.types import Message

from keyboards.menu import main_menu

router = Router()


@router.message(F.text == "💄 Послуги")
async def services(message: Message):
    await message.answer(
        "💄 <b>Наші послуги:</b>\n\n"
        "• Перманент брів (волоскова техніка «Колоски», ефект тіней, комбінована)\n"
        "• Перманент губ\n"
        "• Перманент повік (міжвійка)\n\n"
        "Щоб дізнатися вартість, скористайтеся розділом «💰 Прайс».",
        reply_markup=main_menu,
        parse_mode="HTML"
    )