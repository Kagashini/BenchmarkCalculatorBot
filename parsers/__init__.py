"""
Пакет парсеров benchmark файлов.
Добавляйте новые парсеры для поддержки разных форматов.
"""

from .base_parser import BaseParser
from .capframe_parser import CapFrameParser
from .msi_afterburner_parser import MSIAfterburnerParser
from .custom_parser import CustomParser

# Реестр всех доступных парсеров
PARSER_REGISTRY = {
    "capframex": CapFrameParser,
    "msi_afterburner": MSIAfterburnerParser,
    "custom": CustomParser,
}


def get_parser(parser_type: str) -> BaseParser:
    """Получение парсера по типу"""
    if parser_type not in PARSER_REGISTRY:
        raise ValueError(f"Парсер {parser_type} не найден")
    return PARSER_REGISTRY[parser_type]()


def detect_parser_type(file_content: str) -> str:
    """Автоматическое определение типа парсера по содержимому файла"""
    lines = file_content.split("\n")[:10]  # Анализируем первые 10 строк

    # Проверяем, является ли файл JSON (возможно CapFrameX)
    file_content_stripped = file_content.strip()
    if file_content_stripped.startswith('{') and file_content_stripped.endswith('}'):
        try:
            import json
            data = json.loads(file_content_stripped)
            # Проверяем характерные поля CapFrameX
            if "Hash" in data and "Info" in data and "Runs" in data:
                return "capframex"
        except:
            pass

    # Эвристики для определения формата
    if any("capframex" in line.lower() for line in lines):
        return "capframex"
    elif any("completed," in line and "frames" in line and ".exe" in line for line in lines):
        # Более точная проверка для MSI Afterburner
        return "msi_afterburner"
    elif any("completed," in line and "frames" in line for line in lines):
        # Более общая проверка для Custom формата
        return "custom"
    else:
        return "custom"  # По умолчанию для универсального парсера


__all__ = ["BaseParser", "get_parser", "detect_parser_type", "PARSER_REGISTRY"]
