import logging
import re
import os
import matplotlib.pyplot as plt
import numpy as np
from .analyzer import IDataAnalyzer


def str_to_mbps(x, unit):
    ret = 0.00
    if unit == "K":
        ret = float(x) / 1000
    elif unit == "M":
        ret = float(x)
    elif unit == "G":
        ret = float(x) * 1000
    elif unit == "":
        ret = float(x) / 1000000
    return round(ret, 2)


class Iperf3Analyzer(IDataAnalyzer):
    """Analyze and visualize multiple input iperf3 logs.
    """

    def analyze(self):
        for input_log in self.config.input:
            logging.info(f"Analyze iperf3 log: %s", input_log)
            # if input_log not exist, return False
            if not os.path.exists(input_log):
                logging.info(
                    "The iperf3 log file %s not exist", input_log)
                return False
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
                        logging.info(
                            "The iperf3 %s has too many zero bit", input_log)
                        return False
        return True

    def visualize(self):
        # Implement visualization logic for iperf3 logs
        # ... (visualization code)
        plt.rcParams["font.family"] = "serif"
        plt.xlabel("Time (s)", fontsize=8, fontweight="bold")
        plt.ylabel("Throughput (Mbits/sec)", fontsize=8, fontweight="bold")
        plt.title("Iperf3 throughput analyze", fontsize=10, fontweight="bold")
        for input_log in self.config.input:
            logging.info(f"Visualize iperf3 log: %s", input_log)
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                content = f.read()
                throughput_pattern = r"(\d+) (K|M|G)?Bytes(\s+)(\d+(\.\d+)?) (K|M|G)?bits/sec"
                matches2 = re.findall(throughput_pattern, content)
                throughput_array = [str_to_mbps(
                    match[3], match[5]) for match in matches2]
                if len(throughput_array) <= 1:
                    logging.error(f"no throughput data in %s", input_log)
                    continue
            x = np.arange(1, len(throughput_array))
            plt.plot(x, throughput_array[0: len(x)],
                     'o-', markersize=3, linewidth=1.5, label=f"{input_log}")
            plt.ylim(0, max(throughput_array) + 10)
            plt.legend(loc="lower right", fontsize=8)
        if not self.config.output:
            self.config.output = "iperf3_throughput.svg"
        plt.savefig(f"{self.config.output}")
        logging.info("Visualize iperf3 diagram saved to %s",
                     self.config.output)
