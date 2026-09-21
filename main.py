import asyncio
import logging

from aiogram import Bot, Dispatcher

from config.config import BOT_TOKEN
from database.database import create_database, seed_slots
from handlers.admin import router as admin_router
from handlers.booking import router as booking_router
from handlers.contacts import router as contacts_router
from handlers.price import router as price_router
from handlers.reviews import router as reviews_router
from handlers.services import router as services_router
from handlers.start import router as start_router
from services.scheduler import start_background_scheduler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Реєстрація роутерів
dp.include_router(admin_router)
dp.include_router(start_router)
dp.include_router(services_router)
dp.include_router(price_router)
dp.include_router(contacts_router)
dp.include_router(reviews_router)
dp.include_router(booking_router)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    create_database()
    seed_slots()

    # Фонове автооновлення календаря раз на 12 годин
    asyncio.create_task(start_background_scheduler(interval_hours=12))

    print("🚀 BeautyBot запущений")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())