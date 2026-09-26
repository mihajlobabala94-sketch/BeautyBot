import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "521176880"))  # Замість "YOUR_ADMIN_ID" встав   

if not BOT_TOKEN:
    raise ValueError("Помилка: BOT_TOKEN не знайдено у змінних середовища (.env)!")
