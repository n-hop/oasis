import logging
import re
import os
import matplotlib.pyplot as plt
import numpy as np
from .analyzer import IDataAnalyzer


class FirstRTTAnalyzer(IDataAnalyzer):
    """Analyze and visualize multiple input rtt logs.
    """

    def analyze(self):
        return True

    def visualize(self):
        """
        plot first rtt graph
        """
        plt.rcParams['font.family'] = 'serif'
        plt.xlabel('Time (ms)', fontsize=8,
                   fontweight='bold')
        plt.ylabel('RTT (ms)', fontsize=8,
                   fontweight='bold')
        default_title = "The first TCP message RTT\n"
        default_title += self.config.subtitle
        plt.title(default_title, fontsize=10, fontweight="bold")
        data_first_rtt = {}
        for input_log in self.config.input:
            logging.info(f"Visualize rtt log: %s", input_log)
            # input_log format /a/b/c/iperf3_h1_h2.log
            log_base_name = os.path.basename(input_log)
            first_rtt_list = []
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    first_rtt = re.findall(
                        r'First response from the server, rtt = (\d+)', line)
                    if len(first_rtt) != 0:
                        first_rtt_list.append(int(first_rtt[0]))
                if len(first_rtt_list) == 0:
                    logging.warning(
                        "No first rtt data found in the log file %s", input_log)
                    continue
                # first_rtt_agv
                first_rtt_agv = sum(first_rtt_list) / len(first_rtt_list)
                log_label = log_base_name.split("_")[0]
                data_first_rtt[log_label] = first_rtt_agv
        x = np.array(list(data_first_rtt.keys()))
        y = np.array(list(data_first_rtt.values()))
        plt.bar(x, y, width=0.8, bottom=None)
        plt.xticks(rotation=30, fontsize=5)

        # save the plot to svg file
        if not self.config.output:
            self.config.output = "first_rtt.svg"
        plt.savefig(f"{self.config.output}")
        logging.info("Visualize first rtt diagram saved to %s",
                     self.config.output)
