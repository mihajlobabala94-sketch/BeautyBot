from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


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
            KeyboardButton(text="⚙️ Налаштувати графік"),
            KeyboardButton(text="🔄 Згенерувати на 30 днів")
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

DAYS_NAMES = [
    (0, "Пн"),
    (1, "Вт"),
    (2, "Ср"),
    (3, "Чт"),
    (4, "Пт"),
    (5, "Сб"),
    (6, "Нд"),
]


def get_schedule_settings_keyboard(working_days: list[int]) -> InlineKeyboardMarkup:
    """Генерує інлайн-кнопки перемикання робочих днів та дій з розкладом."""
    days_buttons = []
    current_row = []

    for day_idx, day_name in DAYS_NAMES:
        is_active = day_idx in working_days
        icon = "✅" if is_active else "❌"
        btn_text = f"{icon} {day_name}"
        current_row.append(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"sched_day:{day_idx}"
            )
        )
        if len(current_row) == 4:
            days_buttons.append(current_row)
            current_row = []

    if current_row:
        days_buttons.append(current_row)

    # Кнопки дій
    action_buttons = [
        [
            InlineKeyboardButton(
                text="🕒 Змінити робочі години",
                callback_data="sched_hours_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Згенерувати на 30 днів зараз",
                callback_data="sched_generate_now"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Закрити налаштування",
                callback_data="sched_close"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=days_buttons + action_buttons)


def get_hours_presets_keyboard() -> InlineKeyboardMarkup:
    """Генерує кнопки з готовими шаблонами годин або можливістю ручного введення."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="⏰ 10:00, 12:00, 14:00, 16:00, 18:00",
                callback_data="hours_preset:10,12,14,16,18"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ 09:00, 12:00, 15:00, 18:00",
                callback_data="hours_preset:9,12,15,18"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ 10:00, 13:00, 16:00, 19:00",
                callback_data="hours_preset:10,13,16,19"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Ввести години вручну",
                callback_data="hours_custom_input"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад до графіка",
                callback_data="sched_back_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)