from typing import Dict, Any, List
import pandas as pd
from parsers import get_parser, detect_parser_type


class BenchmarkProcessor:
    """Сервис для обработки benchmark файлов"""

    async def process_files(
        self, file_paths: List[str], parser_type: str = None
    ) -> Dict[str, Any]:
        """
        Обработка нескольких benchmark файлов и объединение результатов
        """
        try:
            all_dataframes = []
            parser_types = []

            # Обрабатываем все файлы
            for file_path in file_paths:
                # Определяем тип парсера если не указан
                if not parser_type:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    detected_parser_type = detect_parser_type(content)
                else:
                    detected_parser_type = parser_type

                parser_types.append(detected_parser_type)

                # Получаем парсер
                parser = get_parser(detected_parser_type)

                # Парсим файл
                df = parser.parse_file(file_path)
                all_dataframes.append(df)

            if not all_dataframes:
                raise ValueError("Не удалось извлечь данные из файлов")

            # Объединяем все данные в один DataFrame
            combined_df = pd.concat(all_dataframes, ignore_index=True)

            # Используем парсер первого файла для дальнейшей обработки
            first_parser_type = parser_types[0] if parser_types else "custom"
            parser = get_parser(first_parser_type)

            # Обрабатываем объединенные данные
            processed_data = parser.process_data(combined_df)

            # Генерируем отчеты
            reports = parser.generate_reports(processed_data)

            return {
                "success": True,
                "parser_type": first_parser_type,
                "reports": reports,
                "stats": processed_data["stats"],
                "raw_count": len(processed_data["raw_data"]),
                "processed_count": len(processed_data["processed_data"]),
                "xlsx_filename": f"benchmark_combined_results.xlsx",
                "csv_filename": f"benchmark_combined_results.csv",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "parser_type": parser_type or "unknown",
            }

    async def process_file(
        self, file_path: str, parser_type: str = None
    ) -> Dict[str, Any]:
        """
        Обработка одного benchmark файла
        """
        try:
            # Определяем тип парсера если не указан
            if not parser_type:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                parser_type = detect_parser_type(content)

            # Получаем парсер
            parser = get_parser(parser_type)

            # Парсим файл
            df = parser.parse_file(file_path)

            if df.empty:
                raise ValueError("Не удалось извлечь данные из файла")

            # Обрабатываем данные
            processed_data = parser.process_data(df)

            # Генерируем отчеты
            reports = parser.generate_reports(processed_data)

            return {
                "success": True,
                "parser_type": parser_type,
                "reports": reports,
                "stats": processed_data["stats"],
                "raw_count": len(processed_data["raw_data"]),
                "processed_count": len(processed_data["processed_data"]),
                "xlsx_filename": f"benchmark_{parser_type}_results.xlsx",
                "csv_filename": f"benchmark_{parser_type}_results.csv",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "parser_type": parser_type or "unknown",
            }

    def get_available_parsers(self) -> Dict[str, str]:
        """Получение списка доступных парсеров"""
        from parsers import PARSER_REGISTRY

        return {
            name: parser.__doc__ or name for name, parser in PARSER_REGISTRY.items()
        }
