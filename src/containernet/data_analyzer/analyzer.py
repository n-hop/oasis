from abc import ABC, abstractmethod


class IDataAnalyzer(ABC):
    @abstractmethod
    def analyze(self, log_file: str):
        pass

    @abstractmethod
    def visualize(self, log_file: str):
        pass
