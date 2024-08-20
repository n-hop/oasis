import logging
import re
import os
import matplotlib.pyplot as plt
import numpy as np
from .analyzer import IDataAnalyzer


class RTTAnalyzer(IDataAnalyzer):
    """Analyze and visualize multiple input rtt logs.
    """

    def analyze(self):
        return True

    def visualize(self):
        """
        plot rtt graph
        """
        data_agv10 = {}
        plt.rcParams['font.family'] = 'serif'
        plt.xlabel('Time (ms)', fontsize=8,
                   fontweight='bold')
        plt.ylabel('RTT (ms)', fontsize=8,
                   fontweight='bold')
        plt.title("RTT analyze", fontsize=10, fontweight="bold")
        max_lines = 0
        x = None
        for input_log in self.config.input:
            logging.info(f"Visualize rtt log: %s", input_log)
            # input_log format /a/b/c/iperf3_h1_h2.log
            log_base_name = os.path.basename(input_log)
            data_agv10[log_base_name] = []
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                lines = f.readlines()
                start_time = 0
                end_time = 0
                interval = 0.00
                for line in lines:
                    if "Start timestamp:" in line:
                        start_time = int(re.findall(
                            r'Start timestamp: (\d+)', line)[0])
                    if "End timestamp:" in line:
                        end_time = int(re.findall(
                            r'End timestamp: (\d+)', line)[0])
                    if "Interval:" in line:
                        interval_list = re.findall(
                            r'Interval: (\d+\.\d+)', line)
                        if interval_list:
                            interval = float(interval_list[0])
                    # print(f"processing line: {lines.index(line)} {line}")
                    average_10 = re.findall(r'average 10: (\d+)', line)
                    if len(average_10) != 0:
                        average_10 = int(average_10[0])
                        average_10 = min(average_10, 5000)
                        data_agv10[log_base_name].append(average_10)
                if len(data_agv10[log_base_name]) == 0:
                    logging.warning(f"no data in %s", log_base_name)
                    continue
                if max_lines == 0:
                    max_lines = len(data_agv10[log_base_name])
                # logging.info(f"max_lines: {max_lines}")
                if len(data_agv10[log_base_name]) < max_lines:
                    # append 4000 instead
                    data_agv10[log_base_name] += [5000] * \
                        (max_lines - len(data_agv10[log_base_name]))
                # start plot x-y graph: x is time in ms,
                log_label = log_base_name.split("_RTT")[0]
                # set x range
                if x is None:
                    x = np.arange(0, (end_time - start_time) *
                                  1000, int(10*interval*1000))
                valid_point_num = min(len(x), len(data_agv10[log_base_name]))
                # logging.info(f"plot : {log_file} valid_point_num: {valid_point_num}")
                plt.plot(x[:valid_point_num], data_agv10[log_base_name][:valid_point_num],
                         label=f"{log_label}")
                plt.legend(loc='upper left', fontsize=8)

        # save the plot to svg file
        if not self.config.output:
            self.config.output = "tcp_rtt.svg"
        plt.savefig(f"{self.config.output}")
        logging.info("Visualize rtt diagram saved to %s",
                     self.config.output)
