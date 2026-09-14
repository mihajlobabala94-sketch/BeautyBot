from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_dates_keyboard(dates: list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    for date in dates:
        builder.button(text=date)

    builder.adjust(2)

    builder.button(text="⬅️ Назад")
    builder.button(text="❌ Скасувати")

    return builder.as_markup(
        resize_keyboard=True
    )