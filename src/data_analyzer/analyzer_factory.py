from .iperf3_analyzer import Iperf3Analyzer
from .analyzer import AnalyzerConfig


class AnalyzerFactory:
    @staticmethod
    def get_analyzer(log_type: str, config: AnalyzerConfig):
        if log_type == "iperf3":
            return Iperf3Analyzer(config)
        raise ValueError(f"Unknown log type: {log_type}")
