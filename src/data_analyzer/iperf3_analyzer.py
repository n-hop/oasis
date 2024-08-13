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
                zero_bit_line_cnt = 0
                lines = f.readlines()
                for line in lines:
                    zero_bit_line = r'0.00 Bytes  0.00 bits/sec'
                    if zero_bit_line in line:
                        zero_bit_line_cnt += 1
                    else:
                        zero_bit_line_cnt = 0
                    if zero_bit_line_cnt > 3:
                        logging.info("The iperf3 %s has too many zero bit", input_log)
                        break

    def visualize(self):
        # Implement visualization logic for iperf3 logs
        # ... (visualization code)
        pass
