from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from pathlib import Path

router = Router()


@router.message(F.text == "📸 Галерея")
async def show_works(message: Message):
    photos_folder = Path("photos")

    if not photos_folder.exists():
        await message.answer("📸 Галерея поки порожня.")
        return

    photos = [
        file for file in photos_folder.iterdir()
        if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ]

    if not photos:
        await message.answer("📸 Галерея поки порожня.")
        return

    await message.answer("📸 Наші роботи:")

    for photo in photos:
        await message.answer_photo(
            photo=FSInputFile(photo),
        )