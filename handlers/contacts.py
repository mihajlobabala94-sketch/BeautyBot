from aiogram import Router, F
from aiogram.types import Message

from keyboards.menu import main_menu

router = Router()


@router.message(F.text == "☎️ Контакти")
async def contacts(message: Message):
    await message.answer(
        "☎️ <b>Контакти майстра</b>\n\n"
        "📞 Телефон: +380992058456\n"
        "📲 Telegram: @beautymaster\n",
        reply_markup=main_menu,
        parse_mode="HTML"
    )


@router.message(F.text.in_({"📍 Адреса", "📍 вулиця Олександра Довженка, 25Б, Івано-Франківськ, Івано-Франківська область, 76000"}))
async def address(message: Message):
    await message.answer(
        "📍 <b>Наша адреса</b>\n\n"
        "м. Івано-Франківськ\n"
        "<a href=\"https://maps.google.com/?q=вул.+Олександра+Довженка+25Б+Івано-Франківськ\">📍 вул. Олександра Довженка, 25Б</a>\n\n"
        "Натисніть на адресу, щоб відкрити на Google Maps 🗺",
        reply_markup=main_menu,
        parse_mode="HTML"
    )