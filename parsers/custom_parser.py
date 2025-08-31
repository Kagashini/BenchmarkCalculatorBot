import pandas as pd
from .base_parser import BaseParser
from typing import List, Dict, Any
import io


class CustomParser(BaseParser):
    """Универсальный парсер для пользовательских форматов benchmark файлов"""

    def parse_file(self, file_path: str) -> pd.DataFrame:
        """
        Парсинг файла. В универсальном парсере мы пытаемся определить формат автоматически.
        """
        # Попробуем разные форматы
        try:
            # CSV формат
            df = pd.read_csv(file_path, encoding="utf-8")
            return df
        except:
            pass

        try:
            # TSV формат
            df = pd.read_csv(file_path, encoding="utf-8", sep="\t")
            return df
        except:
            pass

        try:
            # JSON формат
            df = pd.read_json(file_path)
            return df
        except:
            pass

        # Если не удалось определить формат, возвращаем пустой DataFrame
        return pd.DataFrame()

    def get_supported_formats(self) -> List[str]:
        return [".csv", ".tsv", ".json", ".txt"]

    def can_parse(self, file_content: str) -> bool:
        """
        Универсальный парсер может обрабатывать различные форматы.
        """
        return True

    def process_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Обработка данных после парсинга"""
        if df.empty:
            return {"raw_data": df, "processed_data": df, "stats": {}}

        # Простая обработка - возвращаем как есть
        return {"raw_data": df, "processed_data": df, "stats": self.calculate_stats(df)}

    def calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Расчет базовой статистики"""
        if df.empty:
            return {}

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

        stats = {
            "total_records": len(df),
        }

        for col in numeric_columns:
            stats[f"{col}_avg"] = df[col].mean()
            stats[f"{col}_min"] = df[col].min()
            stats[f"{col}_max"] = df[col].max()

        return stats

    def generate_reports(self, processed_data: Dict[str, Any]) -> Dict[str, bytes]:
        """Генерация отчетов (XLSX и CSV)"""
        df_raw = processed_data["raw_data"]
        df_processed = processed_data["processed_data"]

        # XLSX отчет
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            if not df_raw.empty:
                df_raw.to_excel(writer, sheet_name="Raw Data", index=False)
            if not df_processed.empty:
                df_processed.to_excel(writer, sheet_name="Processed Data", index=False)

            # Добавляем лист со статистикой
            stats_df = pd.DataFrame([processed_data["stats"]])
            if not stats_df.empty:
                stats_df.to_excel(writer, sheet_name="Statistics", index=False)

        excel_buffer.seek(0)

        # CSV отчет
        csv_buffer = io.StringIO()
        if not df_processed.empty:
            df_processed.to_csv(csv_buffer, index=False, encoding="utf-8")

        return {
            "xlsx_data": excel_buffer.getvalue(),
            "csv_data": csv_buffer.getvalue().encode("utf-8")
            if csv_buffer.getvalue()
            else b"",
        }
