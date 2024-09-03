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
        if self.config.data_type == "tcp":
            self.plot_tcp_data()
        elif self.config.data_type == "udp":
            self.plot_udp_data()
        else:
            logging.error("Unsupported data type %s", self.config.data_type)

    def plot_tcp_data(self):
        plt.clf()
        plt.rcParams["font.family"] = "serif"
        plt.xlabel("Time (s)", fontsize=8, fontweight="bold")
        plt.ylabel("Throughput (Mbits/sec)", fontsize=8, fontweight="bold")
        default_title = "Iperf3 throughput \n"
        default_title += self.config.subtitle
        plt.title(default_title, fontsize=10, fontweight="bold")
        max_data_value = 0
        for input_log in self.config.input:
            logging.info(f"Visualize iperf3 log: %s", input_log)
            # input_log format /a/b/c/iperf3_h1_h2.log
            log_base_name = os.path.basename(input_log)
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                content = f.read()
                visualize_data = self.get_tcp_visualize_data(content)
                if len(visualize_data) == {}:
                    logging.error(f"no visualize data in %s", log_base_name)
                    continue
            log_label = log_base_name.split("_")[0]
            for key, data_array in visualize_data.items():
                logging.debug(f"Added %s data: %s  %s",
                              key, data_array, log_base_name)
                cur_max_data_value = max(data_array)
                max_data_value = max(max_data_value, cur_max_data_value)
                x = np.arange(1, len(data_array))
                plt.plot(x, data_array[0: len(x)],
                         'o-', markersize=3, linewidth=1.5, label=f"{log_label}")
                plt.ylim(0, max_data_value + 10)
            plt.legend(loc="lower right", fontsize=8)
        if not self.config.output:
            self.config.output = "iperf3_throughput.svg"
        plt.savefig(f"{self.config.output}")
        logging.info("Visualize iperf3 diagram saved to %s",
                     self.config.output)

    def plot_udp_data(self):
        plt.clf()
        plt.rcParams["font.family"] = "serif"
        # Create 2 subplots in a single column
        fig, axs = plt.subplots(2, 1, figsize=(10, 8))
        fig.suptitle("Iperf3 UDP statistics \n" +
                     self.config.subtitle, fontsize=12, fontweight="bold")
        for input_log in self.config.input:
            logging.info(f"Visualize iperf3 log: %s", input_log)
            log_base_name = os.path.basename(input_log)
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                content = f.read()
                visualize_data = self.get_udp_visualize_data(content)
                if len(visualize_data) == {}:
                    logging.error(f"no visualize data in %s", log_base_name)
                    continue
            log_label = log_base_name.split("_")[0]
            loss_rate_array = visualize_data.get("loss_rate", [])
            max_loss_rate = max(loss_rate_array)
            jitter_array = visualize_data.get("jitter", [])
            x = np.arange(1, len(loss_rate_array))
            # Plot loss rate
            axs[0].plot(x, loss_rate_array[0: len(x)], 'o-',
                        markersize=4, label=f"{log_label}")
            axs[0].set_title('Loss Rate', fontsize=10)
            axs[0].set_xlabel('Time (s)', fontsize=9)
            axs[0].set_ylabel('Loss Rate (%)', fontsize=9)
            axs[0].legend(loc="upper right", fontsize=8)
            axs[0].grid(True)  # Add grid lines for better readability
            if max_loss_rate < 0.5:
                axs[0].set_ylim(-0.5, 0.5)
            else:
                axs[0].set_ylim(-0.5, 1)
            axs[1].plot(x, jitter_array[0: len(x)], 'o-',
                        markersize=4, label=f"{log_label}")
            axs[1].set_title('Jitter', fontsize=10)
            axs[1].set_xlabel('Time (s)', fontsize=9)
            axs[1].set_ylabel('Jitter (ms)', fontsize=9)
            axs[1].legend(loc="upper right", fontsize=8)
            axs[1].grid(True)  # Add grid lines for better readability
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        if not self.config.output:
            self.config.output = "iperf3_udp_statistics.svg"
        plt.savefig(f"{self.config.output}")
        logging.info("Visualize iperf3 diagram saved to %s",
                     self.config.output)

    def get_tcp_visualize_data(self, content):
        visualize_data = {}
        throughput_pattern = r"(\d+) (K|M|G)?Bytes(\s+)(\d+(\.\d+)?) (K|M|G)?bits/sec"
        matches2 = re.findall(throughput_pattern, content)
        throughput_array = [str_to_mbps(
            match[3], match[5]) for match in matches2]
        visualize_data["throughput"] = throughput_array
        return visualize_data

    def get_udp_visualize_data(self, content):
        visualize_data = {}
        loss_rate_pattern = r"ms(\s+)((-)?\d+/\d+)(\s+)\(((-)?\d+(\.\d+)?)%\)"
        jitter_pattern = r"(K|M|G)?bits/sec(\s+)(\d+(\.\d+)?) ms"
        matches4 = re.findall(loss_rate_pattern, content)
        matches2 = re.findall(jitter_pattern, content)
        loss_array = [float(match[4]) for match in matches4 if match[4] != ""]
        jitter_array = [float(match[2])
                        for match in matches2 if match[2] != ""]
        visualize_data["loss_rate"] = loss_array
        visualize_data["jitter"] = jitter_array
        logging.debug(f"loss_rate array: %s", loss_array)
        logging.debug(f"jitter array: %s", jitter_array)
        return visualize_data
