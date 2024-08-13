import logging
import re
import matplotlib.pyplot as plt
import numpy as np
from .analyzer import IDataAnalyzer


def str_to_Mbps(x, unit):
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
            # Implement analysis logic for iperf3 logs
            # ... (analysis code)
            logging.info(f"Analyze iperf3 log: %s", input_log)
            # dump file content
            with open(input_log, "r", encoding="utf-8") as f:
                logging.info(f.read())

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
                throughput_pattern = r"(\d+) (K|M|G)Bytes(\s+)(\d+(\.\d+)?) (K|M|G)bits/sec"
                matches2 = re.findall(throughput_pattern, content)
                throughput_array = [str_to_Mbps(
                    match[3], match[5]) for match in matches2]
                if len(throughput_array) <= 1:
                    logging.error(f"no throughput data in %s", input_log)
                    continue
            x = np.arange(1, len(throughput_array))
            plt.plot(x, throughput_array[0: len(x)],
                     'o-', markersize=3, linewidth=1.5, label=f"{input_log}")
            plt.legend(loc="lower right", fontsize=8)
        # save the plot to svg file
        plt.savefig("name.svg")
        logging.info("Visualize iperf3 diagram saved to name.svg")
