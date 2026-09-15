import sqlite3
from datetime import datetime

DB_NAME = "beautybot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# =========================
# СТВОРЕННЯ БАЗИ
# =========================

def create_database():
    conn = get_connection()
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()


# =========================
# СТАРІ СЛОТИ
# =========================

def remove_old_slots():
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%d.%m.%Y")

    cursor.execute("""
        DELETE FROM available_slots
        WHERE date < ?
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
        INSERT OR IGNORE INTO clients
        (telegram_id, name, phone)
        VALUES (?, ?, ?)
    """, (telegram_id, name, phone))

    # Якщо клієнт вже існує — оновлюємо дані
    cursor.execute("""
        UPDATE clients
        SET name = ?, phone = ?
        WHERE telegram_id = ?
    """, (name, phone, telegram_id))

    conn.commit()
    conn.close()


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


# =========================
# РЕДАГУВАННЯ ЗАПИСУ
# =========================

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

    # Звільняємо старий слот
    cursor.execute("""
        UPDATE available_slots
        SET is_booked = 0
        WHERE date = ? AND time = ?
    """, (old_date, old_time))

    # Оновлюємо клієнта
    cursor.execute("""
        UPDATE clients
        SET name = ?, phone = ?
        WHERE id = ?
    """, (name, phone, client_id))

    # Оновлюємо запис
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

    # Займаємо новий слот
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


def book_slot(date, time):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE available_slots
        SET is_booked = 1
        WHERE date = ?
        AND time = ?
        AND is_booked = 0
    """, (date, time))

    conn.commit()
    conn.close()


# =========================
# ПОЧАТКОВІ СЛОТИ
# =========================

def seed_slots():
    slots = [
        ("21.07.2026", "10:00"),
        ("21.07.2026", "11:00"),
        ("21.07.2026", "12:00"),

        ("22.07.2026", "10:00"),
        ("22.07.2026", "11:00"),

        ("23.07.2026", "15:00"),
        ("23.07.2026", "16:00"),
    ]

    for date, time in slots:
        add_slot(date, time)
        
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
        
        