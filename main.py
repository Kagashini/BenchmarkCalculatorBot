from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from aiogram.exceptions import TelegramUnauthorizedError, TelegramNetworkError
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
import ssl
import os

from config.settings import (
    BOT_TOKEN,
    CUSTOM_API_SERVER,
    WEBHOOK_URL,
    WEBHOOK_PATH,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
)
from handlers import start, file_processing, common

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Проверяем, что токен задан
if not BOT_TOKEN or BOT_TOKEN == "your_actual_bot_token_here":
    logging.error(
        "Не задан действительный токен бота. Пожалуйста, укажите корректный BOT_TOKEN в файле .env"
    )
else:
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
    common.register_common_handlers(dp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan для управления жизненным циклом приложения"""
    if not BOT_TOKEN or BOT_TOKEN == "your_actual_bot_token_here":
        logging.error("Не задан действительный токен бота. Вебхук не будет установлен.")
        yield
        return

    # При запуске
    logging.info(f"Установка вебхука: {WEBHOOK_URL}")
    try:
        await bot.set_webhook(WEBHOOK_URL)
    except TelegramUnauthorizedError:
        logging.error(
            "Неверный токен бота. Пожалуйста, проверьте BOT_TOKEN в файле .env"
        )
    except TelegramNetworkError as e:
        logging.error(f"Ошибка сети при установке вебхука: {e}")
        if CUSTOM_API_SERVER:
            logging.error(
                f"Проверьте, запущен ли локальный сервер на {CUSTOM_API_SERVER}"
            )
    except Exception as e:
        logging.error(f"Ошибка при установке вебхука: {e}")
        import traceback

        logging.error(f"Трассировка ошибки: {traceback.format_exc()}")

    yield

    # При остановке
    try:
        await bot.delete_webhook()
        logging.info("Вебхук удален")
    except Exception as e:
        logging.error(f"Ошибка при удалении вебхука: {e}")


# Создаем FastAPI приложение с lifespan
app = FastAPI(
    title="Benchmark Calculator Bot", docs_url=None, redoc_url=None, lifespan=lifespan
)


@app.get("/", response_class=PlainTextResponse)
async def root():
    """Корневой путь для проверки работы сервера"""
    return "Benchmark Calculator Bot webhook server is running!"


@app.get("/health", response_class=PlainTextResponse)
async def health():
    """Проверка состояния сервера"""
    return "OK"


@app.post("/webhook/{token}")
async def telegram_webhook(request: Request, token: str):
    """Обработчик вебхуков Telegram"""
    if not BOT_TOKEN or BOT_TOKEN == "your_actual_bot_token_here":
        logging.error("Не задан действительный токен бота.")
        raise HTTPException(status_code=500, detail="Неверный токен бота")

    try:
        # Получаем данные из запроса
        update_data = await request.json()

        # Создаем объект Update
        update = Update(**update_data)

        # Обрабатываем обновление
        await dp.feed_update(bot=bot, update=update)

        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Ошибка обработки вебхука: {e}")
        import traceback

        logging.error(f"Трассировка ошибки: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Ошибка обработки вебхука")


def generate_ssl_context():
    """Генерация SSL контекста для сервера"""
    cert_dir = "certs"
    cert_path = os.path.join(cert_dir, "localhost.crt")
    key_path = os.path.join(cert_dir, "localhost.key")

    # Проверяем существование сертификатов
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logging.warning(
            "SSL сертификаты не найдены. Создайте их с помощью ssl_generator.py"
        )
        return None

    # Создаем SSL контекст
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_path, key_path)
    return ssl_context
