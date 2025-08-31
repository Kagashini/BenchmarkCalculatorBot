import pandas as pd
import numpy as np
import xlsxwriter
from xlsxwriter.workbook import Workbook
from datetime import datetime
from .base_parser import BaseParser
from typing import List, Dict, Any
import io


class MSIAfterburnerParser(BaseParser):
    """Парсер для MSI Afterburner benchmark файлов"""

    def parse_file(self, file_path: str) -> pd.DataFrame:
        """Парсинг файла MSI Afterburner и возврат DataFrame"""
        # Read data from the txt file
        with open(file_path, "r", encoding="utf-8") as txt_file:
            data = txt_file.readlines()

        bench_data = []

        for i in range(0, len(data), 6):
            try:
                # Проверяем, что у нас есть достаточно строк для обработки
                if i + 5 >= len(data):
                    continue

                # Extract the data into separate variables
                date_time_info = data[i].split(" ")
                date_string = (
                    date_time_info[0].replace(",", "").replace("\x00", "").strip()
                )
                date = datetime.strptime(date_string, "%d-%m-%Y")
                time = date_time_info[1]

                # Извлекаем имя приложения более надежным способом
                application = "Unknown"
                for j, part in enumerate(date_time_info):
                    if part and ".exe" in part:
                        application = part.replace(".exe", "").strip()
                        break
                    elif part and j > 1 and not part.isspace():
                        # Если не нашли .exe, используем первый непустой элемент
                        application = part.strip()
                        break

                # Ищем индекс 'completed,' более надежным способом
                index_completed = None
                for idx, part in enumerate(date_time_info):
                    if "completed," in part:
                        index_completed = idx
                        break

                # Проверяем, что мы нашли 'completed,' и у нас достаточно элементов
                if index_completed is None or index_completed + 5 >= len(
                    date_time_info
                ):
                    continue

                frames = int(date_time_info[index_completed + 1])
                time_taken = float(date_time_info[index_completed + 5])
                average_framerate = float(
                    data[i + 1].split(":")[1].strip().replace("FPS", "")
                )
                min_framerate = float(
                    data[i + 2]
                    .split(":")[1]
                    .strip()
                    .replace("FPS", "")
                    .replace(",", ".")
                )
                max_framerate = float(
                    data[i + 3]
                    .split(":")[1]
                    .strip()
                    .replace("FPS", "")
                    .replace(",", ".")
                )
                low_1_percent = float(
                    data[i + 4].split(":")[1].strip().replace("FPS", "")
                )
                low_01_percent = float(
                    data[i + 5].split(":")[1].strip().replace("FPS", "")
                )

                # Create a DataFrame
                bench_data.append(
                    {
                        "Date": date,
                        "Time": time,
                        "Application": application,
                        "Frames": frames,
                        "TimeTaken": time_taken,
                        "AverageFramerate": average_framerate,
                        "MinFramerate": min_framerate,
                        "MaxFramerate": max_framerate,
                        "Low1Percent": low_1_percent,
                        "Low01Percent": low_01_percent,
                    }
                )

            except (ValueError, IndexError, datetime.Error) as e:
                # Пропускаем строки с ошибками парсинга
                continue
            except Exception as e:
                # Пропускаем другие ошибки
                continue

        df = pd.DataFrame(bench_data)
        return df

    def get_supported_formats(self) -> List[str]:
        return [".txt", ".benchmark"]

    def can_parse(self, file_content: str) -> bool:
        lines = file_content.split("\n")
        return any("completed," in line and "frames" in line for line in lines)

    def process_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Обработка данных MSI Afterburner"""
        if df.empty:
            return {"raw_data": df, "processed_data": df, "stats": {}}

        # Создаем копию для фильтрации
        df_filtered = df.copy()

        mean_time_taken = df_filtered.groupby(["Date", "Time", "Application"])[
            "TimeTaken"
        ].transform("mean")

        # Filter out the rows where the time taken is more than 30% lower than the mean time taken for that application
        df_filtered = df_filtered[df_filtered["TimeTaken"] >= mean_time_taken * 0.8]
        df_filtered.loc[:, "Time"] = df_filtered["Time"].astype(str).str[:2] + " h"

        # Удаление выбросов с помощью z-оценки
        if len(df_filtered) > 1:  # Только если у нас больше одной записи
            z_scores = np.abs(
                (df_filtered["TimeTaken"] - df_filtered["TimeTaken"].mean())
                / df_filtered["TimeTaken"].std()
            )
            df_filtered = df_filtered[
                z_scores < 3
            ]  # Сохранение только данных в пределах 3-х стандартных отклонений

        # Группировка и усреднение данных
        if not df_filtered.empty:
            mean_data = (
                df_filtered.groupby(["Date", "Time", "Application"], as_index=False)[
                    [
                        "Frames",
                        "TimeTaken",
                        "AverageFramerate",
                        "MinFramerate",
                        "MaxFramerate",
                        "Low1Percent",
                        "Low01Percent",
                    ]
                ]
                .mean()
                .round()
            )

            # Преобразование типов данных
            numeric_columns = [
                "Frames",
                "TimeTaken",
                "AverageFramerate",
                "MinFramerate",
                "MaxFramerate",
                "Low1Percent",
                "Low01Percent",
            ]
            for col in numeric_columns:
                if col in mean_data.columns:
                    mean_data[col] = mean_data[col].astype(int)

            mean_data["Time"] = mean_data["Time"].astype(str)
            mean_data["Application"] = mean_data["Application"].astype(str)
            mean_data = mean_data.sort_values(
                ["Date", "Time", "Application"], ascending=True
            )
        else:
            mean_data = df_filtered.copy()

        return {
            "raw_data": df,
            "processed_data": mean_data,
            "stats": self.calculate_stats(mean_data),
        }

    def calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Расчет статистики для данных MSI Afterburner"""
        if df.empty:
            return {}

        return {
            "avg_framerate": float(df["AverageFramerate"].mean())
            if "AverageFramerate" in df.columns
            else 0,
            "min_framerate": float(df["MinFramerate"].min())
            if "MinFramerate" in df.columns
            else 0,
            "max_framerate": float(df["MaxFramerate"].max())
            if "MaxFramerate" in df.columns
            else 0,
            "total_frames": int(df["Frames"].sum()) if "Frames" in df.columns else 0,
            "total_time": int(df["TimeTaken"].sum())
            if "TimeTaken" in df.columns
            else 0,
        }

    def generate_reports(self, processed_data: Dict[str, Any]) -> Dict[str, bytes]:
        """Генерация отчетов XLSX и CSV для данных MSI Afterburner"""
        df_raw = processed_data["raw_data"]
        df_processed = processed_data["processed_data"]

        # Создание XLSX отчета в памяти
        excel_buffer = io.BytesIO()

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(excel_buffer, engine="xlsxwriter")

        # Write each dataframe to a different worksheet.
        if not df_raw.empty:
            df_raw.to_excel(writer, sheet_name="Benchmark", index=False)
        if not df_processed.empty:
            df_processed.to_excel(writer, sheet_name="Benchmark_mean", index=False)

        # Get the workbook and worksheet objects.
        workbook = writer.book
        worksheet = writer.sheets.get("Benchmark")
        worksheet_mean = writer.sheets.get("Benchmark_mean")

        if worksheet:
            cell_format = workbook.add_format()
            cell_format.set_num_format("dd-mm-yyyy")
            cell_format.set_align("left")
            # Iterate over the 'Date' column and set the date format and alignment for each cell.
            if "Date" in df_raw.columns:
                for row_num, date_value in enumerate(df_raw["Date"], start=2):
                    worksheet.write(f"A{row_num}", date_value, cell_format)
            worksheet.autofit()
            worksheet.set_column("A:A", 12)

        if worksheet_mean:
            cell_format = workbook.add_format()
            cell_format.set_num_format("dd-mm-yyyy")
            cell_format.set_align("left")
            # Iterate over the 'Date' column and set the date format and alignment for each cell.
            if "Date" in df_processed.columns:
                for row_num, date_value in enumerate(df_processed["Date"], start=2):
                    worksheet_mean.write(f"A{row_num}", date_value, cell_format)
            worksheet_mean.autofit()
            worksheet_mean.set_column("A:A", 12)

        # Close the Pandas Excel writer and output the Excel file.
        writer.close()

        excel_buffer.seek(0)

        # Создание CSV отчета
        csv_buffer = io.StringIO()
        if not df_processed.empty:
            df_processed.to_csv(csv_buffer, index=False, encoding="utf-8")

        return {
            "xlsx_data": excel_buffer.getvalue(),
            "csv_data": csv_buffer.getvalue().encode("utf-8") if csv_buffer.getvalue() else b"",
        }
