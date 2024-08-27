from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class AnalyzerConfig:
    input: List[str]   # A series of input files
    output:  str  # The output visualization diagram file
    subtitle: str  # The subtitle of the diagram


class IDataAnalyzer(ABC):
    def __init__(self, config: AnalyzerConfig):
        super().__init__()
        self.config = config

    @abstractmethod
    def analyze(self):
        pass

    @abstractmethod
    def visualize(self):
        pass
