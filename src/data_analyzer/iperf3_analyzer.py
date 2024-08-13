import logging
from .analyzer import IDataAnalyzer


class Iperf3Analyzer(IDataAnalyzer):
    """Analyze and visualize multiple input iperf3 logs.
    """

    def analyze(self):
        for input_log in self.config.input:
            # Implement analysis logic for iperf3 logs
            # ... (analysis code)
            logging.info(f"Analyze iperf3 log: %s", input_log)
            # dump file content
            with open(input_log, "r", encoding="utf-8") as f:
                logging.info(f.read())

    def visualize(self):
        # Implement visualization logic for iperf3 logs
        # ... (visualization code)
        pass
