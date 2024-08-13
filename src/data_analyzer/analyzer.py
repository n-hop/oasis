from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class AnalyzerConfig:
    input: List[str]   # A series of input files
    output:  str  # The output visualization diagram file


class IDataAnalyzer(ABC):
    def __init__(self) -> None:
        self.config = None

    @abstractmethod
    def analyze(self, config: AnalyzerConfig):
        pass

    @abstractmethod
    def visualize(self, config: AnalyzerConfig):
        pass
