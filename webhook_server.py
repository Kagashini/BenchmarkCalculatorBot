import asyncio
import logging
import argparse
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError, TelegramNetworkError
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from config.settings import (
    BOT_TOKEN,
    CUSTOM_API_SERVER
)
from handlers import start, file_processing

# Включаем логирование
logging.basicConfig(level=logging.INFO)


async def start_polling():
    """Запуск бота в режиме поллинга"""
    logging.info("Запуск бота в режиме поллинга")

    # Проверяем, что токен задан
    if not BOT_TOKEN or BOT_TOKEN == "your_actual_bot_token_here":
        logging.error(
            "Не задан действительный токен бота. Пожалуйста, укажите корректный BOT_TOKEN в файле .env"
        )
        return

    try:
        # Создаем сессию с кастомным API сервером, если указан
        if CUSTOM_API_SERVER:
            logging.info(
                f"Попытка подключения к кастомному API серверу: {CUSTOM_API_SERVER}"
            )
            session = AiohttpSession(api=TelegramAPIServer.from_base(CUSTOM_API_SERVER))
            bot = Bot(
                token=BOT_TOKEN,
                session=session,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            logging.info(f"Используется кастомный API сервер: {CUSTOM_API_SERVER}")
        else:
            logging.info("Используется стандартный API сервер Telegram")
            bot = Bot(
                token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )

        dp = Dispatcher()

        # Регистрируем обработчики
        start.register_start_handlers(dp)
        file_processing.register_file_handlers(dp)

        # Проверяем подключение
        bot_info = await bot.get_me()
        logging.info(f"Бот успешно подключен: {bot_info.username}")

        # Удаляем вебхуки и запускаем поллинг
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except TelegramUnauthorizedError:
        logging.error(
            "Неверный токен бота. Пожалуйста, проверьте BOT_TOKEN в файле .env"
        )
    except TelegramNetworkError as e:
        logging.error(f"Ошибка сети при подключении к Telegram API: {e}")
        if CUSTOM_API_SERVER:
            logging.error(
                f"Проверьте, запущен ли локальный сервер на {CUSTOM_API_SERVER}"
            )
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске бота: {e}")
        import traceback

        logging.error(f"Трассировка ошибки: {traceback.format_exc()}")


async def main(mode: str = "polling") -> None:
    """Главная функция для запуска бота"""
    if mode == "webhook":
        logging.error("Вебхуки не поддерживаются в текущей конфигурации")
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
