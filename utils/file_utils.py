import os
import uuid
from aiogram.types import Document
from aiogram import Bot
from config.settings import TEMP_DIR


async def save_uploaded_file(document: Document, bot: Bot) -> str:
    """
    Сохраняет загруженный файл во временную директорию

    Args:
        document: Документ от Telegram
        bot: Экземпляр бота

    Returns:
        str: Путь к сохраненному файлу
    """
    # Создаем временную директорию, если её нет
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Генерируем уникальное имя файла
    file_extension = (
        os.path.splitext(document.file_name)[1] if "." in document.file_name else ""
    )
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(TEMP_DIR, unique_filename)

    # Скачиваем и сохраняем файл
    file_info = await bot.get_file(document.file_id)
    await bot.download_file(file_info.file_path, file_path)

    return file_path


def cleanup_temp_files(*file_paths: str) -> None:
    """
    Удаляет временные файлы

    Args:
        file_paths: Пути к файлам для удаления
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")


def ensure_temp_dir() -> None:
    """Создает временную директорию, если её нет"""
    os.makedirs(TEMP_DIR, exist_ok=True)
