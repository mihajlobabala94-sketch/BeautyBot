from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 Поділитися номером",
                request_contact=True
            )
        ],
        [
            KeyboardButton(text="❌ Скасувати")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

service_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🤎 Брови"),
            KeyboardButton(text="💋 Губи")
        ],
        [
            KeyboardButton(text="👁️ Повіки")
        ],
        [
            KeyboardButton(text="❌ Скасувати")
        ]
    ],
    resize_keyboard=True
)

previous_brows_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Так"),
            KeyboardButton(text="❌ Ні")
        ],
        [
            KeyboardButton(text="❌ Скасувати")
        ]
    ],
    resize_keyboard=True
) 

photo_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="❌ Скасувати")
        ]
    ],
    resize_keyboard=True
)