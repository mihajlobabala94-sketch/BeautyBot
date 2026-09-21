import sqlite3
from datetime import datetime, timedelta

DB_NAME = "beautybot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================
# СТВОРЕННЯ БАЗИ
# =========================

def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode = WAL")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            service TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS available_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            is_booked INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_settings (
            id INTEGER PRIMARY KEY,
            working_days TEXT NOT NULL,
            working_hours TEXT NOT NULL,
            advance_days INTEGER DEFAULT 30,
            auto_generate INTEGER DEFAULT 1
        )
    """)

    # Налаштування за замовчуванням: Пн-Пт, 10:00, 12:00, 14:00, 16:00, 18:00
    cursor.execute("""
        INSERT OR IGNORE INTO schedule_settings (id, working_days, working_hours, advance_days, auto_generate)
        VALUES (1, '0,1,2,3,4', '10:00,12:00,14:00,16:00,18:00', 30, 1)
    """)

    conn.commit()
    conn.close()


# =========================
# НАЛАШТУВАННЯ РОЗКЛАДУ
# =========================

def get_schedule_settings():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT working_days, working_hours, advance_days, auto_generate
        FROM schedule_settings
        WHERE id = 1
    """)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "working_days": [0, 1, 2, 3, 4],
            "working_hours": ["10:00", "12:00", "14:00", "16:00", "18:00"],
            "advance_days": 30,
            "auto_generate": True
        }

    days_str, hours_str, advance_days, auto_generate = row
    days = [int(x) for x in days_str.split(",") if x.strip().isdigit()]
    hours = [x.strip() for x in hours_str.split(",") if x.strip()]

    return {
        "working_days": sorted(days),
        "working_hours": hours,
        "advance_days": advance_days,
        "auto_generate": bool(auto_generate)
    }


def save_schedule_settings(working_days, working_hours, advance_days=30, auto_generate=True):
    conn = get_connection()
    cursor = conn.cursor()

    days_str = ",".join(str(d) for d in sorted(working_days))
    hours_str = ",".join(working_hours)

    cursor.execute("""
        INSERT INTO schedule_settings (id, working_days, working_hours, advance_days, auto_generate)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            working_days = excluded.working_days,
            working_hours = excluded.working_hours,
            advance_days = excluded.advance_days,
            auto_generate = excluded.auto_generate
    """, (days_str, hours_str, advance_days, 1 if auto_generate else 0))

    conn.commit()
    conn.close()


def toggle_schedule_day(day: int):
    settings = get_schedule_settings()
    days = set(settings["working_days"])

    if day in days:
        days.remove(day)
    else:
        days.add(day)

    save_schedule_settings(
        working_days=list(days),
        working_hours=settings["working_hours"],
        advance_days=settings["advance_days"],
        auto_generate=settings["auto_generate"]
    )
    return sorted(days)


def generate_slots_from_settings(advance_days=None) -> int:
    """Генерує вільні слоти на advance_days днів уперед, не перезаписуючи вже зайняті слоти."""
    remove_old_slots()

    settings = get_schedule_settings()
    days = set(settings["working_days"])
    hours = settings["working_hours"]
    days_count = advance_days if advance_days is not None else settings["advance_days"]

    if not days or not hours:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    added_count = 0

    for i in range(days_count):
        current_dt = now + timedelta(days=i)
        if current_dt.weekday() in days:
            date_str = current_dt.strftime("%d.%m.%Y")
            for hour in hours:
                # Якщо це сьогоднішній день, не додаємо минулі години
                if i == 0:
                    try:
                        h_time = datetime.strptime(f"{date_str} {hour}", "%d.%m.%Y %H:%M")
                        if h_time <= now:
                            continue
                    except ValueError:
                        pass

                # Перевіряємо чи такий слот уже існує (вільний чи заброньований)
                cursor.execute("""
                    SELECT id FROM available_slots
                    WHERE date = ? AND time = ?
                """, (date_str, hour))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO available_slots (date, time, is_booked)
                        VALUES (?, ?, 0)
                    """, (date_str, hour))
                    added_count += 1

    conn.commit()
    conn.close()

    return added_count


# =========================
# СТАРІ СЛОТИ
# =========================

def remove_old_slots():
    """Видаляє лише слоти, дата яких вже минула."""
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        DELETE FROM available_slots
        WHERE (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) < ?
    """, (today,))

    conn.commit()
    conn.close()


# =========================
# КЛІЄНТИ
# =========================

def add_client(telegram_id, name, phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO clients (telegram_id, name, phone)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            name = excluded.name,
            phone = excluded.phone
    """, (telegram_id, name, phone))

    cursor.execute("""
        SELECT id
        FROM clients
        WHERE telegram_id = ?
    """, (telegram_id,))

    row = cursor.fetchone()
    client_id = row[0] if row else None

    conn.commit()
    conn.close()

    return client_id


def get_client_id(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM clients
        WHERE telegram_id = ?
    """, (telegram_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def update_client(client_id, name, phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE clients
        SET name = ?, phone = ?
        WHERE id = ?
    """, (name, phone, client_id))

    conn.commit()
    conn.close()


# =========================
# ЗАПИСИ
# =========================

def add_booking(client_id, service, date, time):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bookings
        (client_id, service, date, time)
        VALUES (?, ?, ?, ?)
    """, (client_id, service, date, time))

    conn.commit()
    conn.close()


def get_all_bookings():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            bookings.id,
            bookings.date,
            bookings.time,
            bookings.service,
            clients.name,
            clients.phone
        FROM bookings
        LEFT JOIN clients
        ON bookings.client_id = clients.id
        ORDER BY
            substr(bookings.date, 7, 4),
            substr(bookings.date, 4, 2),
            substr(bookings.date, 1, 2),
            bookings.time
    """)

    result = cursor.fetchall()
    conn.close()

    return result


def get_booking(booking_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            bookings.id,
            bookings.client_id,
            bookings.date,
            bookings.time,
            bookings.service,
            clients.name,
            clients.phone
        FROM bookings
        LEFT JOIN clients
        ON bookings.client_id = clients.id
        WHERE bookings.id = ?
    """, (booking_id,))

    result = cursor.fetchone()
    conn.close()

    return result


def delete_booking(booking_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, time
        FROM bookings
        WHERE id = ?
    """, (booking_id,))

    booking = cursor.fetchone()

    if not booking:
        conn.close()
        return False

    date, time = booking

    cursor.execute("""
        DELETE FROM bookings
        WHERE id = ?
    """, (booking_id,))

    cursor.execute("""
        UPDATE available_slots
        SET is_booked = 0
        WHERE date = ? AND time = ?
    """, (date, time))

    conn.commit()
    conn.close()

    return True


def update_booking(
    booking_id,
    name,
    phone,
    service,
    new_date,
    new_time
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT client_id, date, time
        FROM bookings
        WHERE id = ?
    """, (booking_id,))

    booking = cursor.fetchone()

    if not booking:
        conn.close()
        return False

    client_id, old_date, old_time = booking

    cursor.execute("""
        UPDATE available_slots
        SET is_booked = 0
        WHERE date = ? AND time = ?
    """, (old_date, old_time))

    cursor.execute("""
        UPDATE clients
        SET name = ?, phone = ?
        WHERE id = ?
    """, (name, phone, client_id))

    cursor.execute("""
        UPDATE bookings
        SET service = ?, date = ?, time = ?
        WHERE id = ?
    """, (
        service,
        new_date,
        new_time,
        booking_id
    ))

    cursor.execute("""
        UPDATE available_slots
        SET is_booked = 1
        WHERE date = ? AND time = ?
    """, (new_date, new_time))

    conn.commit()
    conn.close()

    return True


# =========================
# СЛОТИ
# =========================

def add_slot(date, time):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM available_slots
        WHERE date = ? AND time = ?
    """, (date, time))

    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE available_slots
            SET is_booked = 0
            WHERE date = ? AND time = ?
        """, (date, time))
    else:
        cursor.execute("""
            INSERT INTO available_slots
            (date, time, is_booked)
            VALUES (?, ?, 0)
        """, (date, time))

    conn.commit()
    conn.close()


def get_free_dates():
    remove_old_slots()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT date
        FROM available_slots
        WHERE is_booked = 0
        ORDER BY
            substr(date, 7, 4),
            substr(date, 4, 2),
            substr(date, 1, 2)
    """)

    dates = cursor.fetchall()
    conn.close()

    return [x[0] for x in dates]


def get_free_times(date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT time
        FROM available_slots
        WHERE date = ?
        AND is_booked = 0
        ORDER BY time
    """, (date,))

    times = cursor.fetchall()
    conn.close()

    return [x[0] for x in times]


def get_free_slots(date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, time
        FROM available_slots
        WHERE date = ?
        AND is_booked = 0
        ORDER BY time
    """, (date,))

    slots = cursor.fetchall()
    conn.close()

    return slots


def get_slot_by_id(slot_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, time
        FROM available_slots
        WHERE id = ?
        AND is_booked = 0
    """, (slot_id,))

    slot = cursor.fetchone()
    conn.close()

    return slot


def delete_slot_by_id(slot_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM available_slots
        WHERE id = ?
        AND is_booked = 0
    """, (slot_id,))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return deleted


def book_slot(date, time) -> bool:
    """Атомарно бронює слот і повертає True, якщо слот був вільним і заброньований."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE available_slots
        SET is_booked = 1
        WHERE date = ?
        AND time = ?
        AND is_booked = 0
    """, (date, time))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def delete_free_slot(date, time):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM available_slots
        WHERE date = ?
        AND time = ?
        AND is_booked = 0
    """, (date, time))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted > 0


# =========================
# ПОЧАТКОВІ СЛОТИ
# =========================

def seed_slots():
    """Створює демонстраційні слоти на 30 днів уперед, якщо база даних порожня."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM available_slots")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        generate_slots_from_settings(advance_days=30)