import asyncio

from aiogram import Bot, Dispatcher

from config.config import BOT_TOKEN

from handlers.start import router as start_router
from handlers.services import router as services_router
from handlers.contacts import router as contacts_router
from handlers.reviews import router as reviews_router
from handlers.booking import router as booking_router
from handlers.admin import router as admin_router
from handlers.price import router as price_router

from database.database import create_database, seed_slots


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


dp.include_router(start_router)
dp.include_router(services_router)
dp.include_router(contacts_router)
dp.include_router(reviews_router)
dp.include_router(booking_router)
dp.include_router(admin_router)
dp.include_router(price_router)



async def main():

    create_database()
    seed_slots()

    print("🚀 BeautyBot запущений")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())