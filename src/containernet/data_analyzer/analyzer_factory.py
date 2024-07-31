from .iperf3_analyzer import Iperf3Analyzer


class AnalyzerFactory:
    @staticmethod
    def get_analyzer(log_type: str):
        if log_type == "iperf3":
            return Iperf3Analyzer()
        raise ValueError(f"Unknown log type: {log_type}")
