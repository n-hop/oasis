from abc import ABC, abstractmethod


class AnalyzerConfig:
    input: str  # The input file
    output: str  # The output file


class IDataAnalyzer(ABC):
    def __init__(self) -> None:
        self.config = None

    @abstractmethod
    def analyze(self, config: AnalyzerConfig):
        pass

    @abstractmethod
    def visualize(self, config: AnalyzerConfig):
        pass
