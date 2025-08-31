import pandas as pd
from datetime import datetime
from .base_parser import BaseParser
from typing import List


class FrapsParser(BaseParser):
    """Парсер для FRAPS benchmark файлов"""

    def parse_file(self, file_path: str) -> pd.DataFrame:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data = []
        for line in lines:
            if line.strip() and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 2:
                    data.append(
                        {
                            "Date": datetime.now().date(),
                            "Time": datetime.now().time(),
                            "Application": parts[0],
                            "FPS": float(parts[1]),
                            "MinFPS": float(parts[2]) if len(parts) > 2 else 0,
                            "MaxFPS": float(parts[3]) if len(parts) > 3 else 0,
                        }
                    )

        return pd.DataFrame(data)

    def get_supported_formats(self) -> List[str]:
        return [".csv", ".txt", ".fraps"]

    def can_parse(self, file_content: str) -> bool:
        return "FRAPS" in file_content or any(
            line.startswith("#") for line in file_content.split("\n")
        )