from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(F.text == "⭐ Відгуки")
async def reviews(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Переглянути відгуки",
                    url="https://www.google.com/maps/place/Slyvotska+Permanent/@48.9007638,24.6828789,17z/data=!3m1!4b1!4m6!3m5!1s0x4730c10075ea6fc5:0x488995b8698ad2d9!8m2!3d48.9007638!4d24.6854538!16s%2Fg%2F11x8yszstp"
                )
            ]
        ]
    )

    await message.answer(
        "⭐ Відгуки наших клієнтів\n\n"
        "Переглянути відгуки та оцінки майстра можна "
        "на сторінці в Google Maps 👇",
        reply_markup=keyboard
    )