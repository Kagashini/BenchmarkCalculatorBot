from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Any
import io


class BaseParser(ABC):
    """Базовый класс для всех парсеров benchmark файлов"""

    @abstractmethod
    def parse_file(self, file_path: str) -> pd.DataFrame:
        """Парсинг файла и возврат DataFrame"""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Возвращает список поддерживаемых форматов"""
        pass

    @abstractmethod
    def can_parse(self, file_content: str) -> bool:
        """Проверяет, может ли парсер обработать этот файл"""
        pass

    def process_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Обработка данных после парсинга (можно переопределить)"""
        # Базовая обработка - возвращаем как есть
        return {"raw_data": df, "processed_data": df, "stats": self.calculate_stats(df)}

    def calculate_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Расчет базовой статистики"""
        if df.empty:
            return {}

        return {
            "total_records": len(df),
            "avg_framerate": df.get("AverageFramerate", pd.Series([0])).mean(),
            "min_framerate": df.get("MinFramerate", pd.Series([0])).min(),
            "max_framerate": df.get("MaxFramerate", pd.Series([0])).max(),
        }

    def generate_reports(self, processed_data: Dict[str, Any]) -> Dict[str, bytes]:
        """Генерация отчетов (XLSX и CSV)"""
        df_raw = processed_data["raw_data"]
        df_processed = processed_data["processed_data"]

        # XLSX отчет
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df_raw.to_excel(writer, sheet_name="Raw Data", index=False)
            df_processed.to_excel(writer, sheet_name="Processed Data", index=False)

            # Добавляем лист со статистикой
            stats_df = pd.DataFrame([processed_data["stats"]])
            stats_df.to_excel(writer, sheet_name="Statistics", index=False)

        excel_buffer.seek(0)

        # CSV отчет
        csv_buffer = io.StringIO()
        df_processed.to_csv(csv_buffer, index=False, encoding="utf-8")

        return {
            "xlsx_data": excel_buffer.getvalue(),
            "csv_data": csv_buffer.getvalue().encode("utf-8"),
        }