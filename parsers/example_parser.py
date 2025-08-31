# Пример добавления нового парсера
import pandas as pd
from .base_parser import BaseParser


class NewToolParser(BaseParser):
    def parse_file(self, file_path: str) -> pd.DataFrame:
        # ваша логика парсинга
        pass

    def can_parse(self, file_content: str) -> bool:
        # проверка формата
        pass