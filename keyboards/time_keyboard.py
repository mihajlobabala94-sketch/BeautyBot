from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_times_keyboard(times: list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    for time in times:
        builder.button(text=time)

    builder.adjust(2)

    builder.button(text="⬅️ Назад")
    builder.button(text="❌ Скасувати")

    return builder.as_markup(
        resize_keyboard=True
    )