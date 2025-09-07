from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from services.processor import BenchmarkProcessor


async def cmd_start(message: Message):
    """Обработчик команды /start"""
    # Создаем кнопки
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🛠 Парсеры"), KeyboardButton(text="📄 Форматы")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "🎮 Multi-Format Benchmark Processor\n\n"
        "Поддерживаемые форматы:\n"
        "• CapFrameX benchmark\n"
        "• MSI Afterburner\n"
        "• Custom format\n\n"
        "Просто отправьте мне benchmark файл!\n\n"
        "Для CapFrame файлов автоматически объединяются несколько файлов в один отчет.",
        reply_markup=keyboard,
    )


async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📋 Как использовать:\n\n"
        "1. Отправьте benchmark файл\n"
        "2. Бот автоматически определит формат\n"
        "3. Получите детальные отчеты:\n"
        "   • XLSX\n"
        "   • CSV\n\n"
        "📊 Особенности:\n"
        "• Для CapFrameX файлов автоматически объединяются несколько файлов в один отчет\n"
        "• Время отображается в формате часов\n"
        "• Поддерживаются все популярные форматы benchmark!"
    )


async def cmd_about(message: Message):
    """Обработчик кнопки 'О боте'"""
    await message.answer(
        "🎮 Multi-Format Benchmark Processor\n\n"
        "Поддерживаемые форматы:\n"
        "• CapFrameX benchmark\n"
        "• MSI Afterburner\n"
        "• Custom format\n\n"
        "Особенности:\n"
        "• Автоматическое объединение нескольких CapFrameX файлов\n"
        "• Формат времени в часах, без минут и секунд\n"
        "• Генерация отчетов XLSX и CSV\n\n"
        "Просто отправьте мне benchmark файл!"
    )


async def cmd_parsers_info(message: Message):
    """Обработчик кнопки 'Парсеры'"""
    processor = BenchmarkProcessor()
    parsers = processor.get_available_parsers()

    response = "🛠 Доступные парсеры:\n\n"
    for name, description in parsers.items():
        response += f"• {name}: {description}\n"

    response += "\n📁 Бот автоматически определит формат вашего файла!\n"
    response += "Для CapFrameX файлов автоматически объединяются несколько файлов."
    await message.answer(response)


async def cmd_formats_info(message: Message):
    """Обработчик кнопки 'Форматы'"""
    await message.answer(
        "📄 Поддерживаемые форматы файлов:\n\n"
        "<b>CapFrameX</b>\n"
        "Файлы с данными фреймрейтов от CapFrameX\n"
        "Особенности: автоматическое объединение нескольких файлов\n\n"
        "<b>MSI Afterburner</b>\n"
        "Файл benchmark от MSI Afterburner + RivaTuner Statistics Server\n\n"
        "<b>Custom Format</b>\n"
        "Универсальный парсер для различных форматов (CSV, TSV, JSON)"
    )


def register_start_handlers(dp: Dispatcher):
    """Регистрация обработчиков старта"""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_about, lambda message: message.text == "ℹ️ О боте")
    dp.message.register(cmd_help, lambda message: message.text == "❓ Помощь")
    dp.message.register(cmd_parsers_info, lambda message: message.text == "🛠 Парсеры")
    dp.message.register(cmd_formats_info, lambda message: message.text == "📄 Форматы")
