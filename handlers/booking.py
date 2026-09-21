import logging
import re

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config.config import ADMIN_ID as MASTER_ID
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
from keyboards.menu import main_menu
from keyboards.time_keyboard import get_times_keyboard
from states.booking import BookingState

logger = logging.getLogger(__name__)

router = Router()


# =========================
# Скасування з будь-якого стану
# =========================

@router.message(StateFilter("*"), F.text == "❌ Скасувати")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Запис скасовано.",
        reply_markup=main_menu
    )


@router.message(StateFilter("*"), Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Дію скасовано.",
        reply_markup=main_menu
    )


# =========================
# Telegram ID
# =========================

@router.message(Command("id"))
@router.message(F.text == "/id")
async def get_id(message: Message):
    await message.answer(
        f"Ваш Telegram ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )


# =========================
# Початок запису
# =========================

@router.message(F.text == "📅 Записатися")
async def booking_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BookingState.name)

    await message.answer(
        "👤 Як вас звати? Напишіть ваше ім'я:"
    )


# =========================
# Ім'я
# =========================

@router.message(BookingState.name, F.text)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Будь ласка, введіть коректне ім'я:")
        return

    await state.update_data(name=name)
    await state.set_state(BookingState.phone)

    await message.answer(
        "📱 Поділіться номером телефону за допомогою кнопки нижче або введіть його вручну:",
        reply_markup=phone_keyboard
    )


# =========================
# Телефон (Контакт)
# =========================

@router.message(BookingState.phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    await state.update_data(phone=phone)
    await state.set_state(BookingState.service)

    await message.answer(
        "💄 Оберіть процедуру:",
        reply_markup=service_keyboard
    )


# =========================
# Телефон (Текст)
# =========================

@router.message(BookingState.phone, F.text)
async def get_phone_text(message: Message, state: FSMContext):
    raw_text = message.text.strip()
    digits = re.sub(r"\D", "", raw_text)

    if len(digits) < 9:
        await message.answer(
            "⚠️ Номер телефону занадто короткий.\n"
            "Введіть номер у форматі +380XXXXXXXXX або натисніть кнопку «📱 Поділитися номером»:",
            reply_markup=phone_keyboard
        )
        return

    phone = raw_text if raw_text.startswith("+") else (f"+{digits}" if len(digits) > 10 else f"+38{digits}")

    await state.update_data(phone=phone)
    await state.set_state(BookingState.service)

    await message.answer(
        "💄 Оберіть процедуру:",
        reply_markup=service_keyboard
    )


# =========================
# Послуга
# =========================

@router.message(BookingState.service, F.text)
async def get_service(message: Message, state: FSMContext):
    service = message.text.strip()
    await state.update_data(service=service)

    dates = get_free_dates()

    if not dates:
        await message.answer(
            "😔 На жаль, зараз немає вільних дат для запису.\n"
            "Зверніться до майстра напряму в розділі «☎️ Контакти».",
            reply_markup=main_menu
        )
        await state.clear()
        return

    await state.set_state(BookingState.date)

    await message.answer(
        "📅 Оберіть зручну дату:",
        reply_markup=get_dates_keyboard(dates)
    )


# =========================
# Дата
# =========================

@router.message(BookingState.date, F.text)
async def get_date(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(BookingState.service)
        await message.answer(
            "💄 Оберіть процедуру:",
            reply_markup=service_keyboard
        )
        return

    date = message.text.strip()
    free_dates = get_free_dates()

    if date not in free_dates:
        await message.answer(
            "⚠️ Будь ласка, оберіть дату зі списку запропонованих кнопок:",
            reply_markup=get_dates_keyboard(free_dates) if free_dates else main_menu
        )
        if not free_dates:
            await state.clear()
        return

    times = get_free_times(date)

    if not times:
        await message.answer(
            "😔 На цю дату вже немає вільного часу. Оберіть іншу дату:",
            reply_markup=get_dates_keyboard(free_dates)
        )
        return

    await state.update_data(date=date)
    await state.set_state(BookingState.time)

    await message.answer(
        f"📅 Обрано дату: <b>{date}</b>\n🕒 Оберіть зручний час:",
        reply_markup=get_times_keyboard(times),
        parse_mode="HTML"
    )


# =========================
# Час
# =========================

@router.message(BookingState.time, F.text)
async def get_time(message: Message, state: FSMContext):
    data = await state.get_data()
    date = data.get("date")

    if message.text == "⬅️ Назад":
        dates = get_free_dates()
        await state.set_state(BookingState.date)
        await message.answer(
            "📅 Оберіть дату:",
            reply_markup=get_dates_keyboard(dates) if dates else main_menu
        )
        if not dates:
            await state.clear()
        return

    time = message.text.strip()
    times = get_free_times(date)

    if time not in times:
        await message.answer(
            "⚠️ Будь ласка, оберіть час за допомогою кнопок нижче:",
            reply_markup=get_times_keyboard(times)
        )
        return

    # Атомарна спроба забронювати слот
    if not book_slot(date, time):
        remaining_times = get_free_times(date)
        if remaining_times:
            await message.answer(
                "😔 На жаль, цей час щойно забронював інший клієнт.\n"
                "Будь ласка, оберіть інший час:",
                reply_markup=get_times_keyboard(remaining_times)
            )
        else:
            dates = get_free_dates()
            await state.set_state(BookingState.date)
            await message.answer(
                "😔 На цю дату більше немає вільних годин.\n"
                "Будь ласка, оберіть іншу дату:",
                reply_markup=get_dates_keyboard(dates) if dates else main_menu
            )
            if not dates:
                await state.clear()
        return

    await state.update_data(time=time)
    data = await state.get_data()

    # Зберігаємо клієнта
    client_id = add_client(
        telegram_id=message.from_user.id,
        name=data["name"],
        phone=data["phone"]
    )
    if not client_id:
        client_id = get_client_id(message.from_user.id)

    # Зберігаємо бронювання
    add_booking(
        client_id=client_id,
        service=data["service"],
        date=data["date"],
        time=data["time"]
    )

    # Повідомляємо майстра
    username = f"@{message.from_user.username}" if message.from_user.username else "не вказано"
    try:
        await message.bot.send_message(
            MASTER_ID,
            f"🔔 <b>НОВИЙ ЗАПИС!</b>\n\n"
            f"👤 <b>Ім'я:</b> {data['name']}\n"
            f"📞 <b>Телефон:</b> {data['phone']}\n"
            f"💄 <b>Процедура:</b> {data['service']}\n"
            f"📅 <b>Дата:</b> {data['date']}\n"
            f"🕒 <b>Час:</b> {data['time']}\n\n"
            f"📲 <b>Telegram:</b> {username}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не вдалося надіслати сповіщення майстру: {e}")

    # Підтвердження клієнту
    await message.answer(
        f"✅ <b>Ваш запис успішно створено!</b>\n\n"
        f"👤 <b>Ім'я:</b> {data['name']}\n"
        f"📞 <b>Телефон:</b> {data['phone']}\n"
        f"💄 <b>Процедура:</b> {data['service']}\n"
        f"📅 <b>Дата:</b> {data['date']}\n"
        f"🕒 <b>Час:</b> {data['time']}\n\n"
        f"Незабаром майстер зв'яжеться з вами для підтвердження.",
        reply_markup=main_menu,
        parse_mode="HTML"
    )

    await state.clear()