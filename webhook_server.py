from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from aiogram.exceptions import TelegramUnauthorizedError
import ssl
import os

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

# Проверяем, что токен задан
if not BOT_TOKEN or BOT_TOKEN == "your_actual_bot_token_here":
    logging.error(
        "Не задан действительный токен бота. Пожалуйста, укажите корректный BOT_TOKEN в файле .env"
    )
else:
    # Создаем бота и диспетчер
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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
    except Exception as e:
        logging.error(f"Ошибка при установке вебхука: {e}")

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
        raise HTTPException(status_code=500, detail="Ошибка обработки вебхука")


