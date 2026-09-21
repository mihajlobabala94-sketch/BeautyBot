import hashlib
from datetime import datetime

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

from config.config import ADMIN_ID as MASTER_ID
from database.database import (
    add_slot,
    get_free_dates,
    get_free_times,
    get_free_slots,
    get_slot_by_id,
    delete_slot_by_id,
    add_client,
    get_client_id,
    add_booking,
    book_slot,
    get_all_bookings,
    get_booking,
    delete_booking,
    update_booking,
    get_schedule_settings,
    save_schedule_settings,
    toggle_schedule_day,
    generate_slots_from_settings
)
from keyboards.admin import (
    admin_keyboard,
    get_schedule_settings_keyboard,
    get_hours_presets_keyboard,
    DAYS_NAMES
)

router = Router()


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

    # Власні робочі години
    custom_hours = State()


# =========================================================
# КНОПКА ЗАКРИТТЯ
# =========================================================

CLOSE_ADMIN = "❌ Закрити адмін-панель"


# =========================================================
# ПЕРЕВІРКА АДМІНА
# =========================================================

def is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id == MASTER_ID)


def format_schedule_text(settings: dict) -> str:
    days_dict = dict(DAYS_NAMES)
    working_days_text = ", ".join([days_dict[d] for d in settings["working_days"]]) if settings["working_days"] else "Всі дні вихідні"
    hours_text = ", ".join(settings["working_hours"]) if settings["working_hours"] else "Не вказано"

    return (
        "⚙️ <b>НАЛАШТУВАННЯ РОБОЧОГО ГРАФІКА</b>\n\n"
        f"🗓 <b>Робочі дні:</b> {working_days_text}\n"
        f"🕒 <b>Робочі години:</b> {hours_text}\n"
        f"📅 <b>Автогенерація:</b> на {settings['advance_days']} днів уперед\n\n"
        "👇 <i>Натискайте на кнопки днів нижче, щоб увімкнути (✅) або вимкнути (❌):</i>"
    )


# =========================================================
# /admin
# =========================================================

@router.message(F.text == "/admin")
async def admin_start(
    message: Message,
    state: FSMContext
):
    if not is_admin(message):
        await message.answer("⛔ У вас немає доступу.")
        return

    await state.clear()

    await message.answer(
        "🔐 <b>АДМІН-ПАНЕЛЬ</b>\n\n"
        "Оберіть потрібну дію:",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
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
# ⚙️ КОНСТРУКТОР ГРАФІКА ТА АВТОГЕНЕРАЦІЯ
# =========================================================

@router.message(F.text == "⚙️ Налаштувати графік")
async def schedule_menu(
    message: Message,
    state: FSMContext
):
    if not is_admin(message):
        return

    await state.clear()
    settings = get_schedule_settings()

    await message.answer(
        format_schedule_text(settings),
        reply_markup=get_schedule_settings_keyboard(settings["working_days"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sched_day:"))
async def schedule_toggle_day(callback: CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        return

    day_idx = int(callback.data.split(":")[1])
    toggle_schedule_day(day_idx)

    settings = get_schedule_settings()
    await callback.message.edit_text(
        format_schedule_text(settings),
        reply_markup=get_schedule_settings_keyboard(settings["working_days"]),
        parse_mode="HTML"
    )
    await callback.answer("Графік оновлено")


@router.callback_query(F.data == "sched_hours_menu")
async def schedule_hours_menu(callback: CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        return

    await callback.message.edit_text(
        "🕒 <b>Оберіть готовий шаблон робочих годин</b>\n"
        "або натисніть «Ввести години вручну»:",
        reply_markup=get_hours_presets_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hours_preset:"))
async def schedule_hours_preset_apply(callback: CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        return

    preset_str = callback.data.split(":", 1)[1]
    presets = {
        "10,12,14,16,18": ["10:00", "12:00", "14:00", "16:00", "18:00"],
        "9,12,15,18": ["09:00", "12:00", "15:00", "18:00"],
        "10,13,16,19": ["10:00", "13:00", "16:00", "19:00"]
    }
    selected_hours = presets.get(preset_str, ["10:00", "12:00", "14:00", "16:00", "18:00"])

    settings = get_schedule_settings()
    save_schedule_settings(
        working_days=settings["working_days"],
        working_hours=selected_hours,
        advance_days=settings["advance_days"],
        auto_generate=settings["auto_generate"]
    )

    updated_settings = get_schedule_settings()
    await callback.message.edit_text(
        format_schedule_text(updated_settings),
        reply_markup=get_schedule_settings_keyboard(updated_settings["working_days"]),
        parse_mode="HTML"
    )
    await callback.answer("Години збережено ✅")


@router.callback_query(F.data == "hours_custom_input")
async def schedule_hours_custom_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != MASTER_ID:
        return

    await state.set_state(AdminState.custom_hours)
    await callback.message.answer(
        "✏️ Введіть години прийому через кому або пробіл.\n\n"
        "Наприклад:\n"
        "<code>10:00, 11:30, 14:00, 16:30, 18:00</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminState.custom_hours, F.text != CLOSE_ADMIN)
async def schedule_hours_custom_save(message: Message, state: FSMContext):
    raw_text = message.text.replace(";", ",").replace(" ", ",")
    parts = [p.strip() for p in raw_text.split(",") if p.strip()]

    valid_hours = []
    for p in parts:
        try:
            # Форматування та валідація часу
            t = datetime.strptime(p, "%H:%M")
            valid_hours.append(t.strftime("%H:%M"))
        except ValueError:
            pass

    if not valid_hours:
        await message.answer(
            "❌ Не вдалося розпізнати години. Спробуйте ще раз у форматі:\n"
            "<code>10:00, 13:00, 16:00</code>",
            parse_mode="HTML"
        )
        return

    valid_hours = sorted(list(set(valid_hours)))
    settings = get_schedule_settings()
    save_schedule_settings(
        working_days=settings["working_days"],
        working_hours=valid_hours,
        advance_days=settings["advance_days"],
        auto_generate=settings["auto_generate"]
    )

    await state.clear()
    updated_settings = get_schedule_settings()

    await message.answer(
        f"✅ Години оновлено: <b>{', '.join(valid_hours)}</b>\n\n"
        + format_schedule_text(updated_settings),
        reply_markup=get_schedule_settings_keyboard(updated_settings["working_days"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "sched_back_menu")
async def schedule_back_menu(callback: CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        return

    settings = get_schedule_settings()
    await callback.message.edit_text(
        format_schedule_text(settings),
        reply_markup=get_schedule_settings_keyboard(settings["working_days"]),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "sched_close")
async def schedule_close(callback: CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        return

    await callback.message.delete()
    await callback.message.answer(
        "🔐 Адмін-панель",
        reply_markup=admin_keyboard
    )
    await callback.answer()


# =========================================================
# 🔄 ГЕНЕРАЦІЯ СЛОТІВ НА 30 ДНІВ
# =========================================================

@router.message(F.text == "🔄 Згенерувати на 30 днів")
async def generate_slots_btn(message: Message):
    if not is_admin(message):
        return

    added = generate_slots_from_settings(advance_days=30)
    await message.answer(
        "✅ <b>Календар оновлено!</b>\n\n"
        f"Додано нових слотів на 30 днів: <b>{added}</b>\n"
        "Зайняті слоти та існуючі записи збережено без змін.",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "sched_generate_now")
async def generate_slots_callback(callback: CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        return

    added = generate_slots_from_settings(advance_days=30)
    await callback.answer(
        f"✅ Створено {added} нових слотів на 30 днів!",
        show_alert=True
    )

    settings = get_schedule_settings()
    await callback.message.edit_text(
        format_schedule_text(settings) + f"\n\n✨ <i>Щойно додано {added} нових слотів!</i>",
        reply_markup=get_schedule_settings_keyboard(settings["working_days"]),
        parse_mode="HTML"
    )


# =========================================================
# ➕ ДОДАТИ ВІЛЬНИЙ ЧАС ВРУЧНУ
# =========================================================

@router.message(F.text == "➕ Додати вільний час")
async def add_slot_start(
    message: Message,
    state: FSMContext
):
    if not is_admin(message):
        return

    await state.clear()
    await state.set_state(AdminState.add_date)

    await message.answer(
        "📅 Введіть дату у форматі ДД.ММ.РРРР:\n\n"
        "Наприклад:\n"
        "30.09.2026"
    )


@router.message(
    AdminState.add_date,
    F.text != CLOSE_ADMIN
)
async def add_slot_date(
    message: Message,
    state: FSMContext
):
    text = message.text.strip()

    try:
        parsed_date = datetime.strptime(text, "%d.%m.%Y")
        if parsed_date.date() < datetime.now().date():
            await message.answer("⚠️ Дата не може бути в минулому. Введіть майбутню дату (наприклад: 30.09.2026):")
            return
    except ValueError:
        await message.answer("❌ Невірний формат дати. Введіть дату у форматі ДД.ММ.РРРР (наприклад: 30.09.2026):")
        return

    await state.update_data(add_date=text)
    await state.set_state(AdminState.add_time)

    await message.answer(
        "🕐 Введіть час у форматі ГГ:ХХ:\n\n"
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
    text = message.text.strip()

    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await message.answer("❌ Невірний формат часу. Введіть час у форматі ГГ:ХХ (наприклад: 14:00):")
        return

    data = await state.get_data()
    date = data["add_date"]
    time = text

    add_slot(date, time)
    await state.clear()

    await message.answer(
        "✅ Вільний час додано!\n\n"
        f"📅 {date}\n"
        f"🕐 {time}",
        reply_markup=admin_keyboard
    )


# =========================================================
# 📅 ПЕРЕГЛЯНУТИ ВІЛЬНИЙ ЧАС / 🗑 ВИДАЛИТИ ВІЛЬНИЙ ЧАС
# =========================================================

@router.message(F.text.in_({"📅 Переглянути вільний час", "🗑 Видалити вільний час"}))
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
            "😔 Вільних слотів немає.\n"
            "Ви можете швидко згенерувати їх через кнопку «🔄 Згенерувати на 30 днів».",
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
        "Оберіть дату, щоб переглянути години або видалити їх:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


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
    slots = get_free_slots(date)

    if not slots:
        await callback.answer(
            "❌ На цю дату немає вільного часу.",
            show_alert=True
        )
        return

    keyboard_rows = []

    for slot_id, time in slots:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"🕐 {time}",
                callback_data=f"free_info:{slot_id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"free_delete:{slot_id}"
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
    F.data.startswith("free_info:")
)
async def free_time_info(
    callback: CallbackQuery
):
    slot_id = int(callback.data.split(":")[1])
    slot = get_slot_by_id(slot_id)

    if not slot:
        await callback.answer(
            "❌ Слот не знайдено або вже зайнято.",
            show_alert=True
        )
        return

    date, time = slot
    await callback.answer(
        f"📅 {date}\n🕐 {time}",
        show_alert=True
    )


# =========================================================
# 🗑 ОДРАЗУ ВИДАЛИТИ ВІЛЬНИЙ ЧАС
# =========================================================

@router.callback_query(
    F.data.startswith("free_delete:")
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

    slot_id = int(callback.data.split(":")[1])
    slot = get_slot_by_id(slot_id)

    if not slot:
        await callback.answer(
            "❌ Цей слот уже видалений або зайнятий.",
            show_alert=True
        )
        return

    date, time = slot
    delete_slot_by_id(slot_id)

    times = get_free_slots(date)
    keyboard_rows = []

    for current_slot_id, current_time in times:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"🕐 {current_time}",
                callback_data=f"free_info:{current_slot_id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"free_delete:{current_slot_id}"
            )
        ])

    keyboard_rows.append([
        InlineKeyboardButton(
            text="⬅️ До дат",
            callback_data="free_back_dates"
        )
    ])

    if times:
        await callback.message.edit_text(
            f"📅 <b>{date}</b>\n\n"
            "🕐 <b>Вільні години:</b>\n\n"
            "🗑 — видалити годину",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard_rows
            ),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"📅 <b>{date}</b>\n\n"
            "😔 Вільних годин на цю дату більше немає.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="⬅️ До дат",
                        callback_data="free_back_dates"
                    )
                ]]
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
            "😔 Вільних слотів більше немає.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="🔄 Оновити",
                        callback_data="free_back_dates"
                    )
                ]]
            )
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
        "📋 <b>ВСІ ЗАПИСИ:</b>",
        parse_mode="HTML"
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
            f"📅 <b>{date}</b> о <b>{time}</b>\n"
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
            reply_markup=keyboard,
            parse_mode="HTML"
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

    booking_id = int(callback.data.split(":")[1])
    booking = get_booking(booking_id)

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
                    callback_data=f"cancel_yes:{booking_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Ні",
                    callback_data=f"cancel_no:{booking_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "⚠️ <b>Точно хочете скасувати цей запис?</b>\n\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"💄 {service}\n"
        f"📅 {date}\n"
        f"🕐 {time}",
        reply_markup=keyboard,
        parse_mode="HTML"
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

    booking_id = int(callback.data.split(":")[1])
    booking = get_booking(booking_id)

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

    delete_booking(booking_id)

    await callback.message.edit_text(
        "✅ <b>ЗАПИС СКАСОВАНО</b>\n\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"💄 {service}\n"
        f"📅 {date}\n"
        f"🕐 {time}\n\n"
        "🟢 Цей час знову доступний у календарі.",
        parse_mode="HTML"
    )

    await callback.answer("Запис скасовано ✅")


@router.callback_query(
    F.data.startswith("cancel_no:")
)
async def cancel_no(
    callback: CallbackQuery
):
    booking_id = int(callback.data.split(":")[1])
    booking = get_booking(booking_id)

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

    booking_id = int(callback.data.split(":")[1])
    booking = get_booking(booking_id)

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
        "✏️ <b>РЕДАГУВАННЯ ЗАПИСУ</b>\n\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}\n"
        f"💄 {data['service']}\n"
        f"📅 {data['new_date']}\n"
        f"🕐 {data['new_time']}\n\n"
        "⚠️ Зміни поки НЕ збережені.",
        reply_markup=keyboard,
        parse_mode="HTML"
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
    await state.set_state(AdminState.edit_name)
    await callback.message.answer("👤 Введіть нове ім'я:")
    await callback.answer()


@router.message(
    AdminState.edit_name,
    F.text != CLOSE_ADMIN
)
async def edit_name_finish(
    message: Message,
    state: FSMContext
):
    await state.update_data(name=message.text.strip())
    await state.set_state(None)
    await show_edit_menu(message, state)


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
    await state.set_state(AdminState.edit_phone)
    await callback.message.answer("📞 Введіть новий номер:")
    await callback.answer()


@router.message(
    AdminState.edit_phone,
    F.text != CLOSE_ADMIN
)
async def edit_phone_finish(
    message: Message,
    state: FSMContext
):
    await state.update_data(phone=message.text.strip())
    await state.set_state(None)
    await show_edit_menu(message, state)


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
    await state.set_state(AdminState.edit_service)
    await callback.message.answer("💄 Введіть нову процедуру:")
    await callback.answer()


@router.message(
    AdminState.edit_service,
    F.text != CLOSE_ADMIN
)
async def edit_service_finish(
    message: Message,
    state: FSMContext
):
    await state.update_data(service=message.text.strip())
    await state.set_state(None)
    await show_edit_menu(message, state)


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
    await state.set_state(AdminState.edit_date)
    await callback.message.answer(
        "📅 Введіть нову дату у форматі ДД.ММ.РРРР:\n\n"
        "Наприклад:\n"
        "30.09.2026"
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
    date = message.text.strip()

    try:
        datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        await message.answer("❌ Невірний формат дати. Введіть дату у форматі ДД.ММ.РРРР (наприклад: 30.09.2026):")
        return

    data = await state.get_data()
    times = get_free_times(date)

    if date != data["old_date"] and not times:
        await message.answer("❌ На цю дату немає вільного часу.")
        return

    await state.update_data(new_date=date)
    await state.set_state(None)
    await show_edit_menu(message, state)


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

    if date == data["old_date"] and data["old_time"] not in times:
        times.append(data["old_time"])

    if not times:
        await callback.message.answer("❌ На цю дату немає вільного часу.")
        await callback.answer()
        return

    await state.set_state(AdminState.edit_time)
    await callback.message.answer(
        "🕐 Введіть новий час:\n\n" + "\n".join(sorted(times))
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
    time = message.text.strip()

    times = get_free_times(date)
    if date == data["old_date"] and time == data["old_time"]:
        allowed = True
    else:
        allowed = time in times

    if not allowed:
        await message.answer("❌ Цей час вже зайнятий або такого часу немає.")
        return

    await state.update_data(new_time=time)
    await state.set_state(None)
    await show_edit_menu(message, state)


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
        "✅ <b>ЗМІНИ ЗБЕРЕЖЕНО!</b>\n\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}\n"
        f"💄 {data['service']}\n"
        f"📅 {data['new_date']}\n"
        f"🕐 {data['new_time']}",
        parse_mode="HTML"
    )

    await callback.message.answer(
        "🔐 Адмін-панель",
        reply_markup=admin_keyboard
    )

    await callback.answer("Збережено ✅")


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

    await callback.answer("Скасовано")


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
    await state.set_state(AdminState.booking_name)

    await message.answer("👤 Введіть ім'я клієнта:")


@router.message(
    AdminState.booking_name,
    F.text != CLOSE_ADMIN
)
async def create_booking_name(
    message: Message,
    state: FSMContext
):
    await state.update_data(booking_name=message.text.strip())
    await state.set_state(AdminState.booking_phone)
    await message.answer("📞 Введіть номер телефону:")


@router.message(
    AdminState.booking_phone,
    F.text != CLOSE_ADMIN
)
async def create_booking_phone(
    message: Message,
    state: FSMContext
):
    await state.update_data(booking_phone=message.text.strip())
    await state.set_state(AdminState.booking_service)
    await message.answer("💄 Введіть процедуру:")


@router.message(
    AdminState.booking_service,
    F.text != CLOSE_ADMIN
)
async def create_booking_service(
    message: Message,
    state: FSMContext
):
    await state.update_data(booking_service=message.text.strip())
    await state.set_state(AdminState.booking_date)
    await message.answer("📅 Введіть дату у форматі ДД.ММ.РРРР:")


@router.message(
    AdminState.booking_date,
    F.text != CLOSE_ADMIN
)
async def create_booking_date(
    message: Message,
    state: FSMContext
):
    date = message.text.strip()

    try:
        datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        await message.answer("❌ Невірний формат дати. Введіть дату у форматі ДД.ММ.РРРР (наприклад: 30.09.2026):")
        return

    times = get_free_times(date)

    if not times:
        await message.answer(
            "❌ На цю дату немає вільного часу.\n\n"
            "Додайте його через «➕ Додати вільний час»."
        )
        return

    await state.update_data(booking_date=date)
    await state.set_state(AdminState.booking_time)

    await message.answer(
        "🕐 Введіть час:\n\n" + "\n".join(times)
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
    time = message.text.strip()

    if time not in get_free_times(date):
        await message.answer("❌ Цей час уже зайнятий або його немає у списку.")
        return

    # Генеруємо стабільний детермінований ID для клієнта без Telegram облікового запису
    phone_digits = "".join(filter(str.isdigit, data["booking_phone"]))
    if len(phone_digits) >= 9:
        telegram_id = -int(phone_digits[-9:])
    else:
        telegram_id = -int(hashlib.md5(data["booking_phone"].encode()).hexdigest()[:8], 16)

    client_id = add_client(
        telegram_id=telegram_id,
        name=data["booking_name"],
        phone=data["booking_phone"]
    )

    if not client_id:
        client_id = get_client_id(telegram_id)

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
        "✅ <b>ЗАПИС СТВОРЕНО!</b>\n\n"
        f"👤 {data['booking_name']}\n"
        f"📞 {data['booking_phone']}\n"
        f"💄 {data['booking_service']}\n"
        f"📅 {date}\n"
        f"🕐 {time}\n\n"
        "🔴 Час заблоковано у системі.",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )