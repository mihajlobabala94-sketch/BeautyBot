import asyncio
import logging

from database.database import generate_slots_from_settings, remove_old_slots

logger = logging.getLogger(__name__)


async def start_background_scheduler(interval_hours: int = 12):
    """
    Фонове завдання, яке раз на interval_hours годин:
    1. Видаляє слоти, що вже минули.
    2. Автоматично підтримує актуальний розклад на 30 днів уперед.
    """
    logger.info("🕒 Фоновий планувальник розкладу запущено.")

    while True:
        try:
            # Очищення старих слотів
            remove_old_slots()

            # Догенерація слотів на 30 днів
            added = generate_slots_from_settings(advance_days=30)
            if added > 0:
                logger.info(f"✨ Планувальник: автоматично створено {added} нових слотів на 30 днів уперед.")
            else:
                logger.debug("Планувальник: актуальні слоти вже згенеровані.")

        except Exception as e:
            logger.error(f"❌ Помилка у роботі фонового планувальника: {e}")

        # Чекаємо до наступної перевірки
        await asyncio.sleep(interval_hours * 3600)

