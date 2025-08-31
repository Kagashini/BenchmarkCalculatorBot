import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Параметры вебхука
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/")
if BOT_TOKEN and BOT_TOKEN != "your_actual_bot_token_here":
    WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", f"/{BOT_TOKEN}")

WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL", f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_PATH}"
)

# Режим работы (polling или webhook)
RUN_MODE = os.getenv("RUN_MODE", "polling")

# Временная директория для файлов
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_files")

# Создаем временную директорию, если её нет
os.makedirs(TEMP_DIR, exist_ok=True)
