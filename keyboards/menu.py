from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📅 Записатися"),
            KeyboardButton(text="💄 Послуги")
        ],
        [
            KeyboardButton(text="💰 Прайс"),
            KeyboardButton(text="📸 Галерея")
        ],
        [
            KeyboardButton(text="📍 Адреса"),
            KeyboardButton(text="☎️ Контакти")
        ],
        [
            KeyboardButton(text="⭐ Відгуки"),
            KeyboardButton(text="❓ Часті запитання")
        ],
        [
    KeyboardButton(text="⚠️ Протипоказання")
        ]   
    ],
    resize_keyboard=True
)