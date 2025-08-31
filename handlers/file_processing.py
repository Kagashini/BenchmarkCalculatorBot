from aiogram import Dispatcher, F, Bot
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.processor import BenchmarkProcessor
from utils.file_utils import save_uploaded_file, cleanup_temp_files
from parsers import detect_parser_type
import asyncio
import os

processor = BenchmarkProcessor()


# Определяем состояния для обработки нескольких файлов CapFrame
class CapFrameProcessingStates(StatesGroup):
    collecting_files = State()  # Состояние сбора файлов


# Хранилище для временных файлов (в реальном приложении лучше использовать БД или Redis)
capframe_sessions = {}


async def handle_benchmark_file(message: Message, state: FSMContext, bot: Bot):
    """Обработка benchmark файла с автоматическим определением нескольких файлов CapFrame"""
    try:
        # Проверяем размер файла (ограничение Telegram - 50 МБ для обычных пользователей)
        if message.document.file_size > 50 * 1024 * 1024:
            await message.answer(
                "❌ Файл слишком большой. Максимальный размер: 50MB (ограничение Telegram)"
            )
            return

        # Получаем информацию о файле
        file_info = await bot.get_file(message.document.file_id)

        # Проверяем, является ли путь абсолютным (локальный режим)
        if os.path.isabs(file_info.file_path):
            # В локальном режиме file_path уже содержит абсолютный путь к файлу
            file_path = file_info.file_path
        else:
            # В стандартном режиме скачиваем файл
            file_path = await save_uploaded_file(message.document, bot)

        # Определяем тип парсера
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        parser_type = detect_parser_type(content)

        # Проверяем, является ли файл CapFrame
        if parser_type == "capframe":
            # Получаем текущую сессию пользователя
            user_id = message.from_user.id
            session = capframe_sessions.get(user_id, [])
            session.append(file_path)
            capframe_sessions[user_id] = session

            # Если это первый файл, запускаем таймер
            if len(session) == 1:
                # Запускаем задачу для обработки через 10 секунд
                asyncio.create_task(
                    process_capframe_session(user_id, message, state, bot)
                )
                await message.answer(
                    "📥 Получены CapFrameX файлы. Начинаю обработку..."
                )
            return

        # Если это не CapFrame файл, обрабатываем как обычно
        result = await processor.process_file(file_path, parser_type)

        if not result["success"]:
            await message.answer(
                f"❌ Ошибка обработки ({result['parser_type']}): {result['error']}"
            )
            # Очищаем временные файлы только в стандартном режиме
            if not os.path.isabs(file_path):
                cleanup_temp_files(file_path)
            return

        # Отправляем результаты
        await message.answer(
            f"✅ Обработка завершена! ({result['parser_type']})\n"
            f"📊 Записей: {result['raw_count']} → {result['processed_count']}\n"
            f"📈 Средний FPS: {result['stats'].get('avg_framerate', 0):.1f}"
        )

        # Отправляем файлы с проверкой размера
        xlsx_data = result["reports"]["xlsx_data"]
        csv_data = result["reports"]["csv_data"]

        # Проверяем размер файлов перед отправкой
        if len(xlsx_data) > 50 * 1024 * 1024:  # 50 MB
            await message.answer(
                "❌ XLSX отчет слишком большой для отправки через Telegram (более 50MB)"
            )
        else:
            xlsx_file = BufferedInputFile(xlsx_data, filename=result["xlsx_filename"])
            await message.answer_document(document=xlsx_file, caption="📊 XLSX отчет")

        if len(csv_data) > 50 * 1024 * 1024:  # 50 MB
            await message.answer(
                "❌ CSV отчет слишком большой для отправки через Telegram (более 50MB)"
            )
        else:
            csv_file = BufferedInputFile(csv_data, filename=result["csv_filename"])
            await message.answer_document(document=csv_file, caption="📄 CSV отчет")

        # Очищаем временные файлы только в стандартном режиме
        if not os.path.isabs(file_path):
            cleanup_temp_files(file_path)

    except Exception as e:
        await message.answer("❌ Произошла ошибка при обработке файла")
        print(f"Error: {e}")


async def process_capframe_session(
    user_id: int, message: Message, state: FSMContext, bot: Bot
):
    """Обработка сессии CapFrame файлов"""
    # Ждем 10 секунд для получения всех файлов
    await asyncio.sleep(10)

    # Получаем все файлы сессии
    session = capframe_sessions.get(user_id, [])

    if not session:
        return

    try:
        # Обрабатываем все CapFrame файлы как один набор
        result = await processor.process_files(session, "capframe")

        if not result["success"]:
            await message.answer(
                f"❌ Ошибка обработки CapFrame файлов: {result['error']}"
            )
            # Очищаем временные файлы только в стандартном режиме
            for file_path in session:
                if not os.path.isabs(file_path):
                    cleanup_temp_files(file_path)
            # Очищаем сессию
            if user_id in capframe_sessions:
                del capframe_sessions[user_id]
            return

        # Отправляем результаты
        await message.answer(
            f"✅ Обработка CapFrameX файлов завершена!\n"
            f"📊 Записей: {result['raw_count']} → {result['processed_count']}\n"
            f"📈 Средний FPS: {result['stats'].get('avg_framerate', 0):.1f}"
        )

        # Отправляем файлы с проверкой размера
        xlsx_data = result["reports"]["xlsx_data"]
        csv_data = result["reports"]["csv_data"]

        # Проверяем размер файлов перед отправкой
        if len(xlsx_data) > 50 * 1024 * 1024:  # 50 MB
            await message.answer(
                "❌ XLSX отчет слишком большой для отправки через Telegram (более 50MB)"
            )
        else:
            xlsx_file = BufferedInputFile(xlsx_data, filename=result["xlsx_filename"])
            await message.answer_document(
                document=xlsx_file, caption="📊 XLSX отчет (объединенный)"
            )

        if len(csv_data) > 50 * 1024 * 1024:  # 50 MB
            await message.answer(
                "❌ CSV отчет слишком большой для отправки через Telegram (более 50MB)"
            )
        else:
            csv_file = BufferedInputFile(csv_data, filename=result["csv_filename"])
            await message.answer_document(
                document=csv_file, caption="📄 CSV отчет (объединенный)"
            )

        # Очищаем временные файлы только в стандартном режиме
        for file_path in session:
            if not os.path.isabs(file_path):
                cleanup_temp_files(file_path)

        # Очищаем сессию
        if user_id in capframe_sessions:
            del capframe_sessions[user_id]

    except Exception as e:
        await message.answer("❌ Произошла ошибка при обработке CapFrame файлов")
        print(f"Error: {e}")
        # Очищаем сессию в случае ошибки
        if user_id in capframe_sessions:
            # Очищаем временные файлы только в стандартном режиме
            for file_path in capframe_sessions[user_id]:
                if not os.path.isabs(file_path):
                    cleanup_temp_files(file_path)
            del capframe_sessions[user_id]


async def cmd_parsers(message: Message):
    """Показать доступные парсеры"""
    parsers = processor.get_available_parsers()

    response = "🛠 Доступные парсеры:\n\n"
    for name, description in parsers.items():
        response += f"• {name}: {description}\n"

    response += "\n📁 Бот автоматически определит формат вашего файла!"
    await message.answer(response)


def register_file_handlers(dp: Dispatcher):
    """Регистрация обработчиков файлов"""
    # Обработка всех текстовых файлов
    dp.message.register(handle_benchmark_file, F.document)

    # Команда для просмотра парсеров
    dp.message.register(cmd_parsers, Command("parsers"))
