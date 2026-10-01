from aiogram import Router, F
from aiogram.types import Message

from keyboards.menu import main_menu

router = Router()


@router.message(F.text == "☎️ Контакти")
async def contacts(message: Message):
    await message.answer(
        "☎️ <b>Контакти майстра</b>\n\n"
        "📞 Телефон: +380992058456\n"
        "📲 Telegram: @slyvkaolenka\n",
        reply_markup=main_menu,
        parse_mode="HTML"
    )


@router.message(F.text.in_({"📍 Адреса", "📍 вулиця Олександра Довженка, 25Б, Івано-Франківськ, Івано-Франківська область, 76000"}))
async def address(message: Message):
    await message.answer(
        "📍 <b>Наша адреса</b>\n\n"
        "м. Івано-Франківськ\n"
        "<a href=\"https://www.google.com/maps/place/Slyvotska+Permanent/@48.9007638,24.6828789,17z/data=!3m1!4b1!4m6!3m5!1s0x4730c10075ea6fc5:0x488995b8698ad2d9!8m2!3d48.9007638!4d24.6854538!16s%2Fg%2F11x8yszstp\">📍 Slyvotska Permanent — Google Maps</a>\n\n"
        "Натисніть на адресу, щоб відкрити Google Maps 🗺",
        reply_markup=main_menu,
        parse_mode="HTML"
    )