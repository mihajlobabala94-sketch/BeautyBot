from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from database.database import (
    get_free_dates,
    get_free_times,
    add_client,
    get_client_id,
    add_booking,
    book_slot
)

from keyboards.booking import phone_keyboard, service_keyboard
from keyboards.date_keyboard import get_dates_keyboard
from keyboards.time_keyboard import get_times_keyboard
from states.booking import BookingState


router = Router()

# Telegram ID майстра
MASTER_ID = 1132869946


# =========================
# Telegram ID
# =========================

@router.message(F.text == "/id")
async def get_id(message: Message):
    await message.answer(
        f"Ваш Telegram ID: {message.from_user.id}"
    )


# =========================
# Початок запису
# =========================

@router.message(F.text == "📅 Записатися")
async def booking_start(message: Message, state: FSMContext):
    await state.set_state(BookingState.name)

    await message.answer(
        "👤 Як вас звати?"
    )


# =========================
# Ім'я
# =========================

@router.message(BookingState.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(
        name=message.text
    )

    await state.set_state(
        BookingState.phone
    )

    await message.answer(
        "📱 Натисніть кнопку нижче, щоб поділитися номером телефону.",
        reply_markup=phone_keyboard
    )


# =========================
# Телефон
# =========================

@router.message(BookingState.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(
        phone=message.contact.phone_number
    )

    await state.set_state(
        BookingState.service
    )

    await message.answer(
        "💄 Оберіть процедуру:",
        reply_markup=service_keyboard
    )


# =========================
# Послуга
# =========================

@router.message(BookingState.service)
async def get_service(message: Message, state: FSMContext):
    await state.update_data(
        service=message.text
    )

    dates = get_free_dates()

    if not dates:
        await message.answer(
            "😔 На жаль, зараз немає вільних дат."
        )
        await state.clear()
        return

    await state.set_state(
        BookingState.date
    )

    await message.answer(
        "📅 Оберіть дату:",
        reply_markup=get_dates_keyboard(dates)
    )


# =========================
# Дата
# =========================

@router.message(BookingState.date)
async def get_date(message: Message, state: FSMContext):

    if message.text == "❌ Скасувати":
        await cancel(message, state)
        return

    if message.text == "⬅️ Назад":
        await state.set_state(
            BookingState.service
        )

        await message.answer(
            "💄 Оберіть процедуру:",
            reply_markup=service_keyboard
        )
        return

    await state.update_data(
        date=message.text
    )

    times = get_free_times(
        message.text
    )

    if not times:
        await message.answer(
            "😔 На цю дату вже немає вільного часу."
        )
        return

    await state.set_state(
        BookingState.time
    )

    await message.answer(
        "🕒 Оберіть час:",
        reply_markup=get_times_keyboard(times)
    )


# =========================
# Час
# =========================

@router.message(BookingState.time)
async def get_time(message: Message, state: FSMContext):

    if message.text == "❌ Скасувати":
        await cancel(message, state)
        return

    if message.text == "⬅️ Назад":
        dates = get_free_dates()

        await state.set_state(
            BookingState.date
        )

        await message.answer(
            "📅 Оберіть дату:",
            reply_markup=get_dates_keyboard(dates)
        )
        return

    await state.update_data(
        time=message.text
    )

    data = await state.get_data()

    # =========================
    # Зберігаємо клієнта
    # =========================

    add_client(
        telegram_id=message.from_user.id,
        name=data["name"],
        phone=data["phone"]
    )

    # =========================
    # Отримуємо ID клієнта
    # =========================

    client_id = get_client_id(
        message.from_user.id
    )

    # =========================
    # Зберігаємо бронювання
    # =========================

    add_booking(
        client_id=client_id,
        service=data["service"],
        date=data["date"],
        time=data["time"]
    )

    # =========================
    # Робимо слот зайнятим
    # =========================

    book_slot(
        date=data["date"],
        time=data["time"]
    )

    # =========================
    # Повідомляємо майстра
    # =========================

    username = message.from_user.username

    if username:
        client_username = f"@{username}"
    else:
        client_username = "немає username"

    await message.bot.send_message(
        MASTER_ID,
        f"""
🔔 НОВИЙ ЗАПИС!

👤 Ім'я: {data["name"]}
📞 Телефон: {data["phone"]}
💄 Процедура: {data["service"]}
📅 Дата: {data["date"]}
🕒 Час: {data["time"]}

📲 Telegram: {client_username}
"""
    )

    # =========================
    # Підтвердження клієнту
    # =========================

    await message.answer(
        f"""
✅ Ваш запис успішно створено!

👤 {data["name"]}
📞 {data["phone"]}
💄 {data["service"]}
📅 {data["date"]}
🕒 {data["time"]}

Незабаром майстер підтвердить запис.
""",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.clear()


# =========================
# Скасування
# =========================

@router.message(F.text == "❌ Скасувати")
async def cancel(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "❌ Запис скасовано.",
        reply_markup=ReplyKeyboardRemove()
    )