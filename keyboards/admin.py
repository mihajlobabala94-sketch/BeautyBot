from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Додати вільний час"),
            KeyboardButton(text="🗑 Видалити вільний час")
        ],
        [
            KeyboardButton(text="📅 Переглянути вільний час")
        ],
        [
            KeyboardButton(text="➕ Створити запис"),
            KeyboardButton(text="📋 Переглянути записи")
        ],
        [
            KeyboardButton(text="❌ Закрити адмін-панель")
        ]
    ],
    resize_keyboard=True
)