import asyncio
import logging
import argparse
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError

from config.settings import (
    BOT_TOKEN,
    WEBHOOK_URL,
    WEBHOOK_PATH,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
)
from handlers import start, file_processing, common

# Включаем логирование
logging.basicConfig(level=logging.INFO)


async def start_polling():
    """Запуск бота в режиме поллинга"""
    logging.info("Запуск бота в режиме поллинга")

    # Проверяем, что токен задан
    if not BOT_TOKEN or BOT_TOKEN == "your_actual_bot_token_here":
        logging.error("Не задан действительный токен бота. Пожалуйста, укажите корректный BOT_TOKEN в файле .env")
        return

    # Создаем бота и диспетчер
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Регистрируем обработчики
    start.register_start_handlers(dp)
    file_processing.register_file_handlers(dp)
    common.register_common_handlers(dp)

    try:
        # Удаляем вебхуки и запускаем поллинг
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except TelegramUnauthorizedError:
        logging.error("Неверный токен бота. Пожалуйста, проверьте BOT_TOKEN в файле .env")
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске бота: {e}")


async def start_webhook():
    """Запуск бота в режиме вебхуков"""
    logging.info("Запуск бота в режиме вебхуков")

    from webhook_server import app

    # Запускаем сервер
    config = uvicorn.Config(
        app="webhook_server:app",
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main(mode: str = "polling") -> None:
    """Главная функция для запуска бота"""
    if mode == "webhook":
        await start_webhook()
    else:
        await start_polling()


if __name__ == "__main__":
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description="Запуск Benchmark Calculator Bot")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["polling", "webhook"],
        default="polling",
        help="Режим работы бота: polling или webhook",
    )

    args = parser.parse_args()

    # Запускаем бота
    asyncio.run(main(args.mode))
