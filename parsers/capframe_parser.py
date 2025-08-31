import pandas as pd
import json
from datetime import datetime
import math
from .base_parser import BaseParser
from typing import List, Dict, Any
import io
import numpy as np


class CapFrameParser(BaseParser):
    """Парсер для CapFrameX benchmark файлов"""

    def parse_file(self, file_path: str) -> pd.DataFrame:
        """Парсинг файла CapFrameX и возврат DataFrame"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Некорректный JSON формат: {str(e)}")
        except Exception as e:
            raise ValueError(f"Ошибка чтения файла: {str(e)}")

        bench_data = []

        # Извлекаем информацию из JSON
        info = data.get("Info", {})
        runs = data.get("Runs", [])

        if not runs:
            raise ValueError("Файл не содержит данных о прогонах (Runs)")

        process_name = info.get("ProcessName", "Unknown").replace(".exe", "")
        creation_date = info.get("CreationDate", "")

        # Парсим дату
        if creation_date:
            try:
                # Обрабатываем различные форматы дат
                if creation_date.endswith("Z"):
                    dt = datetime.fromisoformat(creation_date[:-1] + "+00:00")
                else:
                    dt = datetime.fromisoformat(creation_date)
                date = dt.date()
                time_obj = dt.time()
            except Exception:
                date = datetime.now().date()
                time_obj = datetime.now().time()
        else:
            date = datetime.now().date()
            time_obj = datetime.now().time()

        # Округляем часы вниз
        hour = math.floor(time_obj.hour)

        # Собираем все данные из всех прогонов
        all_time_values = []
        total_time_taken = 0.0

        for run_idx, run in enumerate(runs):
            try:
                capture_data = run.get("CaptureData", {})
                time_in_seconds = capture_data.get("TimeInSeconds", [])
                if time_in_seconds:
                    all_time_values.extend(time_in_seconds)
                    # TimeTaken - это время последнего кадра
                    total_time_taken += time_in_seconds[-1]
            except Exception:
                # Пропускаем проблемные прогоны
                continue

        # Если есть данные, обрабатываем их
        if all_time_values and len(all_time_values) > 1:
            # Сортируем временные значения
            all_time_values.sort()

            # Вычисляем FPS для каждого кадра
            fps_values = []
            for i in range(1, len(all_time_values)):
                delta = all_time_values[i] - all_time_values[i - 1]
                if delta > 0:
                    fps_values.append(1.0 / delta)

            if fps_values:
                avg_fps = sum(fps_values) / len(fps_values)
                min_fps = min(fps_values)
                max_fps = max(fps_values)

                # Вычисляем 1% lows
                sorted_fps = sorted(fps_values)
                low_1_percent_index = max(0, int(len(sorted_fps) * 0.01))
                low_1_percent = sorted_fps[low_1_percent_index]

                # Вычисляем 0.1% lows
                low_01_percent_index = max(0, int(len(sorted_fps) * 0.001))
                low_01_percent = sorted_fps[low_01_percent_index]

                bench_data.append(
                    {
                        "Date": date,
                        "Time": f"{hour:02d}",  # Часы с ведущим нулем и округлением вниз
                        "Application": process_name,
                        "Frames": len(all_time_values),
                        "TimeTaken": total_time_taken,  # Общее время выполнения всех прогонов
                        "AverageFramerate": avg_fps,
                        "MinFramerate": min_fps,
                        "MaxFramerate": max_fps,
                        "Low1Percent": low_1_percent,
                        "Low01Percent": low_01_percent,
                    }
                )

        if not bench_data:
            raise ValueError("Не удалось извлечь данные из файла")

        return pd.DataFrame(bench_data)

    def get_supported_formats(self) -> List[str]:
        return [".json"]

    def can_parse(self, file_content: str) -> bool:
        try:
            # Проверяем, начинается и заканчивается ли содержимое как JSON
            stripped_content = file_content.strip()
            if not (
                stripped_content.startswith("{") and stripped_content.endswith("}")
            ):
                return False

            data = json.loads(stripped_content)
            # Проверяем, есть ли характерные поля CapFrame
            return (
                "Hash" in data
                and "Info" in data
                and "Runs" in data
                and isinstance(data.get("Runs"), list)
            )
        except:
            return False

    def process_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Обработка данных CapFrameX"""
        if df.empty:
            return {"raw_data": df, "processed_data": df, "stats": {}}

        # Создаем копию для фильтрации
        df_filtered = df.copy()

        # Применяем фильтрацию по времени выполнения (как в MSI Afterburner)
        if len(df_filtered) > 1:
            mean_time_taken = df_filtered.groupby(["Date", "Time", "Application"])[
                "TimeTaken"
            ].transform("mean")
            df_filtered = df_filtered[df_filtered["TimeTaken"] >= mean_time_taken * 0.8]

        df_filtered.loc[:, "Time"] = df_filtered["Time"].astype(str) + " h"

        # Удаление выбросов с помощью z-оценки (как в MSI Afterburner)
        if len(df_filtered) > 1:  # Только если у нас больше одной записи
            z_scores = np.abs(
                (df_filtered["TimeTaken"] - df_filtered["TimeTaken"].mean())
                / df_filtered["TimeTaken"].std()
            )
            df_filtered = df_filtered[
                z_scores < 3
            ]  # Сохранение только данных в пределах 3-х стандартных отклонений

        # Группировка и усреднение данных (как в MSI Afterburner)
        if not df_filtered.empty and len(df_filtered) > 1:
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
        elif not df_filtered.empty:
            # Если только одна запись, просто копируем данные
            mean_data = df_filtered.copy()
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
        else:
            mean_data = pd.DataFrame()

        return {
            "raw_data": df,
            "processed_data": mean_data,
            "stats": self.calculate_stats(mean_data if not mean_data.empty else df),
        }

    def calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Расчет статистики для данных CapFrameX"""
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
        """Генерация отчетов XLSX и CSV для данных CapFrameX"""
        df_raw = processed_data["raw_data"]
        df_processed = processed_data["processed_data"]

        # Создание XLSX отчета в памяти
        excel_buffer = io.BytesIO()

        try:
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                # Запись данных на разные листы (аналогично MSI Afterburner)
                if not df_raw.empty:
                    df_raw.to_excel(writer, sheet_name="Benchmark", index=False)
                if not df_processed.empty:
                    df_processed.to_excel(
                        writer, sheet_name="Benchmark_mean", index=False
                    )

                # Получение объектов workbook и worksheet
                workbook = writer.book
                worksheet = writer.sheets.get("Benchmark")
                worksheet_mean = writer.sheets.get("Benchmark_mean")

                # Форматирование дат (аналогично MSI Afterburner)
                if worksheet and not df_raw.empty and "Date" in df_raw.columns:
                    cell_format = workbook.add_format()
                    cell_format.set_num_format("dd-mm-yyyy")
                    cell_format.set_align("left")
                    for row_num, date_value in enumerate(df_raw["Date"], start=2):
                        worksheet.write(f"A{row_num}", date_value, cell_format)
                    worksheet.autofit()
                    worksheet.set_column("A:A", 12)

                if (
                    worksheet_mean
                    and not df_processed.empty
                    and "Date" in df_processed.columns
                ):
                    cell_format = workbook.add_format()
                    cell_format.set_num_format("dd-mm-yyyy")
                    cell_format.set_align("left")
                    for row_num, date_value in enumerate(df_processed["Date"], start=2):
                        worksheet_mean.write(f"A{row_num}", date_value, cell_format)
                    worksheet_mean.autofit()
                    worksheet_mean.set_column("A:A", 12)

        except Exception as e:
            # В случае ошибки при создании Excel, создаем пустой файл
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                pd.DataFrame().to_excel(writer, sheet_name="Benchmark", index=False)
                pd.DataFrame().to_excel(
                    writer, sheet_name="Benchmark_mean", index=False
                )

        excel_buffer.seek(0)

        # Создание CSV отчета
        csv_buffer = io.StringIO()
        if not df_processed.empty:
            df_processed.to_csv(csv_buffer, index=False, encoding="utf-8")

        return {
            "xlsx_data": excel_buffer.getvalue(),
            "csv_data": csv_buffer.getvalue().encode("utf-8") if csv_buffer.getvalue() else b"",
        }
