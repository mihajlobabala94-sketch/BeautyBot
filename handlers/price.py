from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()


# =========================
# МЕНЮ ПРАЙСУ
# =========================

price_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Перша процедура"),
            KeyboardButton(text="Корекція моєї роботи")
        ],
        [
            KeyboardButton(text="⬅️ Назад")
        ]
    ],
    resize_keyboard=True
)


# =========================
# КНОПКА "💰 Прайс"
# =========================

@router.message(lambda message: message.text == "💰 Прайс")
async def show_price(message: Message):
    await message.answer(
        "💰 <b>Наш прайс</b>\n\n"
        "Оберіть потрібний варіант:",
        reply_markup=price_menu,
        parse_mode="HTML"
    )


# =========================
# ПЕРША ПРОЦЕДУРА
# =========================

@router.message(lambda message: message.text == "Перша процедура")
async def show_first_procedure(message: Message):
    await message.answer(
        "💎 <b>Перша процедура</b>\n\n"
        "✨ <b>Техніки:</b>\n\n"
        "• Брови — волоскова техніка «Колоски» — <b>___ грн</b>\n"
        "• Брови — комбінована техніка — <b>8000 грн</b>\n"
        "• Брови — ефект тіней — <b>5000 грн</b>\n"
        "• Перманент губ — <b>5500 грн</b>\n"
        "• Міжвія — <b>4500 грн</b>",
        parse_mode="HTML"
    )


# =========================
# КОРЕКЦІЯ
# =========================

@router.message(lambda message: message.text == "Корекція моєї роботи")
async def show_correction(message: Message):
    await message.answer(
        "🔄 <b>Корекція моєї роботи</b>\n\n"
        "✨ <b>Ціни:</b>\n\n"
        "• Брови — «Колоски» або комбіновані — <b>4000 грн</b>\n"
        "• Брови — ефект тіней — <b>___ грн</b>\n"
        "• Перманент губ — <b>4000 грн</b>\n"
        "• Міжвія — <b>4000 грн</b>\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "💫 <b>Корекція / поновлення моєї роботи</b>\n"
        "через 3 місяці і далі <b>− 1000 грн</b>\n"
        "від вартості першої процедури.",
        parse_mode="HTML"
    )


# =========================
# НАЗАД
# =========================

@router.message(lambda message: message.text == "⬅️ Назад")
async def back_from_price(message: Message):
    from keyboards.menu import main_menu

    await message.answer(
        "Головне меню:",
        reply_markup=main_menu
    )