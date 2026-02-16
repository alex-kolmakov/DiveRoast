from abc import ABC, abstractmethod

import pandas as pd


class DiveLogParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> pd.DataFrame:
        """Parse a dive log file and return a DataFrame of per-sample dive data."""
        ...

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions (e.g. ['.ssrf', '.xml'])."""
        ...
