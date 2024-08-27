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
        data_rtt_agv10 = {}
        data_rtt_all = {}
        plt.clf()
        plt.rcParams['font.family'] = 'serif'
        plt.xlabel('Time (ms)', fontsize=8,
                   fontweight='bold')
        plt.ylabel('RTT (ms)', fontsize=8,
                   fontweight='bold')
        plt.title("Average RTT for each consecutive 10 packets",
                  fontsize=10, fontweight="bold")
        max_lines = 0
        x = None
        for input_log in self.config.input:
            logging.info(f"Visualize rtt log: %s", input_log)
            log_base_name = os.path.basename(input_log)
            data_rtt_agv10[log_base_name] = []
            data_rtt_all[log_base_name] = []
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
                    average_10 = self.find_agv10_rtt(line)
                    if average_10 is not None:
                        data_rtt_agv10[log_base_name].append(average_10)
                    per_packet_rtt = self.find_per_packet_rtt(line)
                    if per_packet_rtt is not None:
                        data_rtt_all[log_base_name].append(per_packet_rtt)
                if len(data_rtt_agv10[log_base_name]) == 0:
                    logging.warning(
                        f"no avg10 data in %s, lines %s", log_base_name, len(lines))
                    continue
                if len(data_rtt_all[log_base_name]) == 0:
                    logging.warning(
                        f"no per packet rtt data in %s, lines %s", log_base_name, len(lines))
                    continue
                if max_lines == 0:
                    max_lines = len(data_rtt_agv10[log_base_name])
                if len(data_rtt_agv10[log_base_name]) < max_lines:
                    # append 5000 instead
                    data_rtt_agv10[log_base_name] += [5000] * \
                        (max_lines - len(data_rtt_agv10[log_base_name]))
                # start plot x-y graph: x is time in ms,
                log_label = log_base_name.split("_")[0]
                # set x range
                if x is None:
                    x = np.arange(0, (end_time - start_time) *
                                  1000, int(10*interval*1000))
                valid_point_num = min(len(x), len(
                    data_rtt_agv10[log_base_name]))
                # logging.info(f"plot : {log_file} valid_point_num: {valid_point_num}")
                plt.plot(x[:valid_point_num], data_rtt_agv10[log_base_name][:valid_point_num],
                         label=f"{log_label}")
                plt.legend(loc='upper left', fontsize=8)
        if not self.config.output:
            self.config.output = "rtt.svg"
        if '.svg' not in self.config.output:
            plt.savefig(f"{self.config.output}rtt.svg")
            logging.info("Visualize rtt diagram saved to %s",
                         self.config.output)
        else:
            plt.savefig(f"{self.config.output}")
            logging.info("Visualize rtt diagram saved to %s",
                         self.config.output)
        self.plot_rtt_cdf(data_rtt_all)

    def find_agv10_rtt(self, line):
        """
        find the average 10 rtt from the log lines
        """
        average_10 = re.findall(r'average 10: (\d+)', line)
        if len(average_10) != 0:
            average_10 = int(average_10[0])
            average_10 = min(average_10, 5000)
            return average_10
        return None

    def find_per_packet_rtt(self, line):
        """
        find the per packet rtt from the log lines
        """
        per_packet_rtt = re.findall(r'new_rtt = (\d+)', line)
        if len(per_packet_rtt) != 0:
            per_packet_rtt = int(per_packet_rtt[0])
            per_packet_rtt = min(per_packet_rtt, 5000)
            return per_packet_rtt
        return None

    def plot_rtt_cdf(self, rtt_data: dict):
        plt.clf()
        plt.rcParams['font.family'] = 'serif'
        plt.xlabel('RTT (ms)', fontsize=8,
                   fontweight='bold')
        plt.ylabel('Cumulative Probability', fontsize=8,
                   fontweight='bold')
        plt.title(f"RTT of all TCP messages", fontsize=10, fontweight="bold")
        for log_base_name, rtt_list in rtt_data.items():
            if len(rtt_list) == 0:
                logging.warning(
                    f"no per packet rtt data in %s", log_base_name)
                continue
            # Sort the RTT values
            rtt_list.sort()
            # Calculate the cumulative probabilities
            cdf = np.arange(1, len(rtt_list) + 1) / len(rtt_list)
            # Plot the CDF
            log_label = log_base_name.split("_")[0]
            plt.plot(rtt_list, cdf, label=f"{log_label}")
            plt.legend(loc='lower right', fontsize=8)
        # Save the plot to svg file
        if '.svg' not in self.config.output:
            plt.savefig(f"{self.config.output}rtt_cdf.svg")
            logging.info("Visualize RTT CDF diagram saved to %s",
                         self.config.output)
        else:
            path = os.path.dirname(self.config.output)
            plt.savefig(f"{path}rtt_cdf.svg")
            logging.info("Visualize RTT CDF diagram saved to %s",
                         path)
