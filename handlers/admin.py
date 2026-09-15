from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from keyboards.admin import admin_keyboard

from database.database import (
    DB_NAME,
    add_slot,
    get_free_dates,
    get_free_times,
    add_client,
    get_client_id,
    add_booking,
    book_slot,
    get_all_bookings,
    get_booking,
    delete_booking,
    update_booking
)

import sqlite3


router = Router()


# =========================================================
# ID МАЙСТРА
# =========================================================

MASTER_ID = 1132869946


# =========================================================
# СТАНИ
# =========================================================

class AdminState(StatesGroup):

    # Додавання вільного часу
    add_date = State()
    add_time = State()

    # Створення запису
    booking_name = State()
    booking_phone = State()
    booking_service = State()
    booking_date = State()
    booking_time = State()

    # Редагування запису
    edit_name = State()
    edit_phone = State()
    edit_service = State()
    edit_date = State()
    edit_time = State()


# =========================================================
# КНОПКА ЗАКРИТТЯ
# =========================================================

CLOSE_ADMIN = "❌ Закрити адмін-панель"


# =========================================================
# ПЕРЕВІРКА АДМІНА
# =========================================================

def is_admin(message):
    return message.from_user.id == MASTER_ID


# =========================================================
# /admin
# =========================================================

@router.message(F.text == "/admin")
async def admin_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        await message.answer(
            "⛔ У вас немає доступу."
        )
        return

    await state.clear()

    await message.answer(
        "🔐 АДМІН-ПАНЕЛЬ\n\n"
        "Оберіть потрібну дію:",
        reply_markup=admin_keyboard
    )


# =========================================================
# ❌ ЗАКРИТИ АДМІН-ПАНЕЛЬ
# =========================================================

@router.message(F.text == CLOSE_ADMIN)
async def close_admin(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.clear()

    await message.answer(
        "🔒 Адмін-панель закрито.\n\n"
        "Незавершені зміни не збережено.",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ➕ ДОДАТИ ВІЛЬНИЙ ЧАС
# =========================================================

@router.message(F.text == "➕ Додати вільний час")
async def add_slot_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.clear()

    await state.set_state(
        AdminState.add_date
    )

    await message.answer(
        "📅 Введіть дату:\n\n"
        "Наприклад:\n"
        "30.07.2026"
    )


@router.message(
    AdminState.add_date,
    F.text != CLOSE_ADMIN
)
async def add_slot_date(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        add_date=message.text.strip()
    )

    await state.set_state(
        AdminState.add_time
    )

    await message.answer(
        "🕐 Введіть час:\n\n"
        "Наприклад:\n"
        "14:00"
    )


@router.message(
    AdminState.add_time,
    F.text != CLOSE_ADMIN
)
async def add_slot_time(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    date = data["add_date"]
    time = message.text.strip()

    add_slot(
        date,
        time
    )

    await state.clear()

    await message.answer(
        "✅ Вільний час додано!\n\n"
        f"📅 {date}\n"
        f"🕐 {time}",
        reply_markup=admin_keyboard
    )


# =========================================================
# 📅 ПЕРЕГЛЯНУТИ ВІЛЬНИЙ ЧАС
# =========================================================

@router.message(F.text == "📅 Переглянути вільний час")
async def show_free_slots(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.clear()

    dates = get_free_dates()

    if not dates:
        await message.answer(
            "😔 Вільних слотів немає.",
            reply_markup=admin_keyboard
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📅 {date}",
                    callback_data=f"free_date|{date}"
                )
            ]
            for date in dates
        ]
    )

    await message.answer(
        "📅 <b>Календар вільного часу</b>\n\n"
        "Оберіть дату:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================================================
# 📅 ВИБІР ДАТИ
# =========================================================

@router.callback_query(
    F.data.startswith("free_date|")
)
async def show_free_times(
    callback: CallbackQuery
):

    if callback.from_user.id != MASTER_ID:
        await callback.answer(
            "⛔ Немає доступу.",
            show_alert=True
        )
        return

    date = callback.data.split("|", 1)[1]

    times = get_free_times(date)

    if not times:
        await callback.answer(
            "❌ На цю дату немає вільного часу.",
            show_alert=True
        )
        return

    keyboard_rows = []

    for time in sorted(times):
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"🕐 {time}",
                callback_data=f"free_info|{date}|{time}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"free_delete|{date}|{time}"
            )
        ])

    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ До дат",
            callback_data="free_back_dates"
        )
    ])

    await callback.message.edit_text(
        f"📅 <b>{date}</b>\n\n"
        "🕐 <b>Вільні години:</b>\n\n"
        "🗑 — видалити годину",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard_rows
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# 🕐 ПЕРЕГЛЯД ГОДИНИ
# =========================================================

@router.callback_query(
    F.data.startswith("free_info|")
)
async def free_time_info(
    callback: CallbackQuery
):

    parts = callback.data.split("|", 2)

    date = parts[1]
    time = parts[2]

    await callback.answer(
        f"📅 {date}\n🕐 {time}",
        show_alert=True
    )


# =========================================================
# 🗑 ОДРАЗУ ВИДАЛИТИ ВІЛЬНИЙ ЧАС
# =========================================================

@router.callback_query(
    F.data.startswith("free_delete|")
)
async def delete_free(
    callback: CallbackQuery
):

    if callback.from_user.id != MASTER_ID:
        await callback.answer(
            "⛔ Немає доступу.",
            show_alert=True
        )
        return

    parts = callback.data.split("|", 2)

    date = parts[1]
    time = parts[2]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM available_slots
        WHERE date = ?
        AND time = ?
        AND is_booked = 0
        """,
        (date, time)
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted == 0:
        await callback.answer(
            "❌ Цей час не знайдено або він уже зайнятий.",
            show_alert=True
        )
        return

    times = get_free_times(date)

    if not times:

        dates = get_free_dates()

        if not dates:
            await callback.message.edit_text(
                "😔 Вільних слотів більше немає."
            )
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"📅 {current_date}",
                            callback_data=f"free_date|{current_date}"
                        )
                    ]
                    for current_date in dates
                ]
            )

            await callback.message.edit_text(
                "✅ <b>Годину видалено!</b>\n\n"
                f"📅 {date}\n"
                f"🕐 {time}\n\n"
                "📅 <b>Оберіть іншу дату:</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )

    else:

        keyboard_rows = []

        for current_time in sorted(times):
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"🕐 {current_time}",
                    callback_data=(
                        f"free_info|{date}|{current_time}"
                    )
                ),
                InlineKeyboardButton(
                    text="🗑",
                    callback_data=(
                        f"free_delete|{date}|{current_time}"
                    )
                )
            ])

        keyboard_rows.append([
            InlineKeyboardButton(
                text="⬅️ До дат",
                callback_data="free_back_dates"
            )
        ])

        await callback.message.edit_text(
            f"📅 <b>{date}</b>\n\n"
            "🕐 <b>Вільні години:</b>\n\n"
            "🗑 — видалити годину",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard_rows
            ),
            parse_mode="HTML"
        )

    await callback.answer(
        f"🗑 {time} видалено"
    )


# =========================================================
# ⬅️ НАЗАД ДО ДАТ
# =========================================================

@router.callback_query(
    F.data == "free_back_dates"
)
async def free_back_dates(
    callback: CallbackQuery
):

    if callback.from_user.id != MASTER_ID:
        await callback.answer(
            "⛔ Немає доступу.",
            show_alert=True
        )
        return

    dates = get_free_dates()

    if not dates:
        await callback.message.edit_text(
            "😔 Вільних слотів більше немає."
        )
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📅 {date}",
                    callback_data=f"free_date|{date}"
                )
            ]
            for date in dates
        ]
    )

    await callback.message.edit_text(
        "📅 <b>Календар вільного часу</b>\n\n"
        "Оберіть дату:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# 📋 ПЕРЕГЛЯНУТИ ЗАПИСИ
# =========================================================

@router.message(F.text == "📋 Переглянути записи")
async def show_bookings(
    message: Message
):

    if not is_admin(message):
        return

    bookings = get_all_bookings()

    if not bookings:

        await message.answer(
            "📋 Записів поки немає.",
            reply_markup=admin_keyboard
        )

        return

    await message.answer(
        "📋 ВСІ ЗАПИСИ:"
    )

    for booking in bookings:

        (
            booking_id,
            date,
            time,
            service,
            name,
            phone
        ) = booking

        text = (
            f"📅 {date}\n"
            f"🕐 {time}\n"
            f"👤 {name}\n"
            f"📞 {phone}\n"
            f"💄 {service}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Змінити",
                        callback_data=f"edit:{booking_id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Скасувати",
                        callback_data=f"cancel:{booking_id}"
                    )
                ]
            ]
        )

        await message.answer(
            text,
            reply_markup=keyboard
        )

    await message.answer(
        "🔐 Адмін-панель",
        reply_markup=admin_keyboard
    )


# =========================================================
# ❌ СКАСУВАТИ ЗАПИС
# =========================================================

@router.callback_query(
    F.data.startswith("cancel:")
)
async def cancel_start(
    callback: CallbackQuery
):

    if callback.from_user.id != MASTER_ID:
        return

    booking_id = int(
        callback.data.split(":")[1]
    )

    booking = get_booking(
        booking_id
    )

    if not booking:

        await callback.answer(
            "❌ Запис не знайдено.",
            show_alert=True
        )

        return

    (
        _,
        _,
        date,
        time,
        service,
        name,
        phone
    ) = booking

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Так, скасувати",
                    callback_data=(
                        f"cancel_yes:{booking_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Ні",
                    callback_data=(
                        f"cancel_no:{booking_id}"
                    )
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "⚠️ Точно хочете скасувати цей запис?\n\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"💄 {service}\n"
        f"📅 {date}\n"
        f"🕐 {time}",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("cancel_yes:")
)
async def cancel_yes(
    callback: CallbackQuery
):

    if callback.from_user.id != MASTER_ID:
        return

    booking_id = int(
        callback.data.split(":")[1]
    )

    booking = get_booking(
        booking_id
    )

    if not booking:

        await callback.answer(
            "❌ Запис не знайдено.",
            show_alert=True
        )

        return

    (
        _,
        _,
        date,
        time,
        service,
        name,
        phone
    ) = booking

    delete_booking(
        booking_id
    )

    await callback.message.edit_text(
        "✅ ЗАПИС СКАСОВАНО\n\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"💄 {service}\n"
        f"📅 {date}\n"
        f"🕐 {time}\n\n"
        "🟢 Цей час знову доступний."
    )

    await callback.answer(
        "Запис скасовано ✅"
    )


@router.callback_query(
    F.data.startswith("cancel_no:")
)
async def cancel_no(
    callback: CallbackQuery
):

    booking_id = int(
        callback.data.split(":")[1]
    )

    booking = get_booking(
        booking_id
    )

    if not booking:
        return

    (
        _,
        _,
        date,
        time,
        service,
        name,
        phone
    ) = booking

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Змінити",
                    callback_data=f"edit:{booking_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data=f"cancel:{booking_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"📅 {date}\n"
        f"🕐 {time}\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"💄 {service}",
        reply_markup=keyboard
    )

    await callback.answer()


# =========================================================
# ✏️ РЕДАГУВАННЯ ЗАПИСУ
# =========================================================

@router.callback_query(
    F.data.startswith("edit:")
)
async def edit_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id != MASTER_ID:
        return

    booking_id = int(
        callback.data.split(":")[1]
    )

    booking = get_booking(
        booking_id
    )

    if not booking:

        await callback.answer(
            "❌ Запис не знайдено.",
            show_alert=True
        )

        return

    (
        _,
        client_id,
        date,
        time,
        service,
        name,
        phone
    ) = booking

    await state.clear()

    await state.update_data(
        booking_id=booking_id,
        client_id=client_id,

        old_date=date,
        old_time=time,

        name=name,
        phone=phone,
        service=service,

        new_date=date,
        new_time=time
    )

    await show_edit_menu(
        callback.message,
        state
    )

    await callback.answer()


# =========================================================
# МЕНЮ РЕДАГУВАННЯ
# =========================================================

async def show_edit_menu(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Ім'я",
                    callback_data="edit_field:name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Телефон",
                    callback_data="edit_field:phone"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💄 Процедура",
                    callback_data="edit_field:service"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Дата",
                    callback_data="edit_field:date"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🕐 Час",
                    callback_data="edit_field:time"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💾 Зберегти зміни",
                    callback_data="edit_save"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Скасувати редагування",
                    callback_data="edit_cancel"
                )
            ]
        ]
    )

    await message.answer(
        "✏️ РЕДАГУВАННЯ ЗАПИСУ\n\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}\n"
        f"💄 {data['service']}\n"
        f"📅 {data['new_date']}\n"
        f"🕐 {data['new_time']}\n\n"
        "⚠️ Зміни поки НЕ збережені.",
        reply_markup=keyboard
    )


# =========================================================
# ЗМІНА ІМЕНІ
# =========================================================

@router.callback_query(
    F.data == "edit_field:name"
)
async def edit_name_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        AdminState.edit_name
    )

    await callback.message.answer(
        "👤 Введіть нове ім'я:"
    )

    await callback.answer()


@router.message(
    AdminState.edit_name,
    F.text != CLOSE_ADMIN
)
async def edit_name_finish(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        name=message.text
    )

    await state.set_state(None)

    await show_edit_menu(
        message,
        state
    )


# =========================================================
# ЗМІНА ТЕЛЕФОНУ
# =========================================================

@router.callback_query(
    F.data == "edit_field:phone"
)
async def edit_phone_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        AdminState.edit_phone
    )

    await callback.message.answer(
        "📞 Введіть новий номер:"
    )

    await callback.answer()


@router.message(
    AdminState.edit_phone,
    F.text != CLOSE_ADMIN
)
async def edit_phone_finish(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.text
    )

    await state.set_state(None)

    await show_edit_menu(
        message,
        state
    )


# =========================================================
# ЗМІНА ПРОЦЕДУРИ
# =========================================================

@router.callback_query(
    F.data == "edit_field:service"
)
async def edit_service_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        AdminState.edit_service
    )

    await callback.message.answer(
        "💄 Введіть нову процедуру:"
    )

    await callback.answer()


@router.message(
    AdminState.edit_service,
    F.text != CLOSE_ADMIN
)
async def edit_service_finish(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        service=message.text
    )

    await state.set_state(None)

    await show_edit_menu(
        message,
        state
    )


# =========================================================
# ЗМІНА ДАТИ
# =========================================================

@router.callback_query(
    F.data == "edit_field:date"
)
async def edit_date_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        AdminState.edit_date
    )

    await callback.message.answer(
        "📅 Введіть нову дату:\n\n"
        "Наприклад:\n"
        "30.07.2026"
    )

    await callback.answer()


@router.message(
    AdminState.edit_date,
    F.text != CLOSE_ADMIN
)
async def edit_date_finish(
    message: Message,
    state: FSMContext
):

    date = message.text

    data = await state.get_data()

    times = get_free_times(date)

    if (
        date != data["old_date"]
        and not times
    ):

        await message.answer(
            "❌ На цю дату немає вільного часу."
        )

        return

    await state.update_data(
        new_date=date
    )

    await state.set_state(None)

    await show_edit_menu(
        message,
        state
    )


# =========================================================
# ЗМІНА ЧАСУ
# =========================================================

@router.callback_query(
    F.data == "edit_field:time"
)
async def edit_time_start(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    date = data["new_date"]

    times = get_free_times(date)

    if (
        date == data["old_date"]
        and data["old_time"] not in times
    ):
        times.append(
            data["old_time"]
        )

    if not times:

        await callback.message.answer(
            "❌ На цю дату немає вільного часу."
        )

        await callback.answer()

        return

    await state.set_state(
        AdminState.edit_time
    )

    await callback.message.answer(
        "🕐 Введіть новий час:\n\n"
        + "\n".join(sorted(times))
    )

    await callback.answer()


@router.message(
    AdminState.edit_time,
    F.text != CLOSE_ADMIN
)
async def edit_time_finish(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    date = data["new_date"]
    time = message.text

    times = get_free_times(date)

    if (
        date == data["old_date"]
        and time == data["old_time"]
    ):
        allowed = True
    else:
        allowed = time in times

    if not allowed:

        await message.answer(
            "❌ Цей час вже зайнятий "
            "або такого часу немає."
        )

        return

    await state.update_data(
        new_time=time
    )

    await state.set_state(None)

    await show_edit_menu(
        message,
        state
    )


# =========================================================
# 💾 ЗБЕРЕГТИ РЕДАГУВАННЯ
# =========================================================

@router.callback_query(
    F.data == "edit_save"
)
async def edit_save(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id != MASTER_ID:
        return

    data = await state.get_data()

    if not data:

        await callback.answer(
            "❌ Немає змін.",
            show_alert=True
        )

        return

    update_booking(
        booking_id=data["booking_id"],
        name=data["name"],
        phone=data["phone"],
        service=data["service"],
        new_date=data["new_date"],
        new_time=data["new_time"]
    )

    await state.clear()

    await callback.message.edit_text(
        "✅ ЗМІНИ ЗБЕРЕЖЕНО!\n\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}\n"
        f"💄 {data['service']}\n"
        f"📅 {data['new_date']}\n"
        f"🕐 {data['new_time']}"
    )

    await callback.message.answer(
        "🔐 Адмін-панель",
        reply_markup=admin_keyboard
    )

    await callback.answer(
        "Збережено ✅"
    )


# =========================================================
# ↩️ СКАСУВАТИ РЕДАГУВАННЯ
# =========================================================

@router.callback_query(
    F.data == "edit_cancel"
)
async def edit_cancel(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.message.edit_text(
        "↩️ Редагування скасовано.\n\n"
        "Жодних змін не збережено."
    )

    await callback.message.answer(
        "🔐 Адмін-панель",
        reply_markup=admin_keyboard
    )

    await callback.answer(
        "Скасовано"
    )


# =========================================================
# ➕ СТВОРИТИ ЗАПИС ВРУЧНУ
# =========================================================

@router.message(F.text == "➕ Створити запис")
async def create_booking_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.clear()

    await state.set_state(
        AdminState.booking_name
    )

    await message.answer(
        "👤 Введіть ім'я клієнта:"
    )


@router.message(
    AdminState.booking_name,
    F.text != CLOSE_ADMIN
)
async def create_booking_name(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        booking_name=message.text
    )

    await state.set_state(
        AdminState.booking_phone
    )

    await message.answer(
        "📞 Введіть номер телефону:"
    )


@router.message(
    AdminState.booking_phone,
    F.text != CLOSE_ADMIN
)
async def create_booking_phone(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        booking_phone=message.text
    )

    await state.set_state(
        AdminState.booking_service
    )

    await message.answer(
        "💄 Введіть процедуру:"
    )


@router.message(
    AdminState.booking_service,
    F.text != CLOSE_ADMIN
)
async def create_booking_service(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        booking_service=message.text
    )

    await state.set_state(
        AdminState.booking_date
    )

    await message.answer(
        "📅 Введіть дату:"
    )


@router.message(
    AdminState.booking_date,
    F.text != CLOSE_ADMIN
)
async def create_booking_date(
    message: Message,
    state: FSMContext
):

    date = message.text

    times = get_free_times(
        date
    )

    if not times:

        await message.answer(
            "❌ На цю дату немає вільного часу.\n\n"
            "Додайте його через "
            "➕ Додати вільний час."
        )

        return

    await state.update_data(
        booking_date=date
    )

    await state.set_state(
        AdminState.booking_time
    )

    await message.answer(
        "🕐 Введіть час:\n\n"
        + "\n".join(times)
    )


@router.message(
    AdminState.booking_time,
    F.text != CLOSE_ADMIN
)
async def create_booking_time(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    date = data["booking_date"]
    time = message.text

    if time not in get_free_times(date):

        await message.answer(
            "❌ Цей час уже зайнятий "
            "або його немає."
        )

        return

    telegram_id = -abs(
        hash(data["booking_phone"])
    )

    add_client(
        telegram_id=telegram_id,
        name=data["booking_name"],
        phone=data["booking_phone"]
    )

    client_id = get_client_id(
        telegram_id
    )

    add_booking(
        client_id=client_id,
        service=data["booking_service"],
        date=date,
        time=time
    )

    book_slot(
        date=date,
        time=time
    )

    await state.clear()

    await message.answer(
        "✅ ЗАПИС СТВОРЕНО!\n\n"
        f"👤 {data['booking_name']}\n"
        f"📞 {data['booking_phone']}\n"
        f"💄 {data['booking_service']}\n"
        f"📅 {date}\n"
        f"🕐 {time}\n\n"
        "🔴 Час заблоковано.",
        reply_markup=admin_keyboard
    )