import logging
import re
import os
from enum import IntEnum
import matplotlib.pyplot as plt
import numpy as np
from tools.util import str_to_mbps
from .analyzer import IDataAnalyzer


class PlotColors(IntEnum):
    min_value = 0
    red = 1
    blue = 2
    black = 3
    green = 4
    orange = 5
    max_value = 6

    def __str__(self) -> str:
        if self == PlotColors.red:
            return "red"
        if self == PlotColors.blue:
            return "blue"
        if self == PlotColors.black:
            return "green"
        if self == PlotColors.green:
            return "black"
        if self == PlotColors.orange:
            return "orange"
        return "unknown_color"


PlotColorAndMarkerMap = {
    PlotColors.red: 'o--',
    PlotColors.blue: '^:',
    PlotColors.black: 'x-',
    PlotColors.green: '<--',
    PlotColors.orange: 's-'
}


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
                is_test_finished = False
                for line in lines:
                    if 'receiver' in line:
                        is_test_finished = True
                    zero_bit_line = r'0.00 Bytes  0.00 bits/sec'
                    if zero_bit_line in line:
                        zero_bit_line_cnt += 1
                    else:
                        zero_bit_line_cnt = 0
                    if zero_bit_line_cnt > 3:
                        logging.info(
                            "The iperf3 log %s has too many zero bit lines", input_log)
                        return False
                if not is_test_finished:
                    logging.info(
                        "The iperf3 log %s is not finished", input_log)
                    return False
        return True

    def visualize(self):
        if self.config.data_type == "tcp":
            self.plot_stream_data()
        elif self.config.data_type in ('udp', 'bats'):
            self.plot_datagram_data()
        else:
            logging.error("Unsupported data type: %s", self.config.data_type)

    def plot_stream_data(self):
        plt.clf()
        plt.rcParams["font.family"] = "serif"
        plt.xlabel("Time (s)", fontsize=8, fontweight="bold")
        plt.ylabel("Throughput (Mbits/sec)", fontsize=8, fontweight="bold")
        default_title = "Iperf3 throughput \n"
        default_title += self.config.subtitle
        plt.title(default_title, fontsize=10, fontweight="bold")
        max_data_value = 0
        data_len = 0
        index = PlotColors.min_value + 1
        for input_log in self.config.input:
            if not os.path.exists(input_log):
                continue
            logging.info(f"Visualize iperf3 log: %s", input_log)
            # input_log format /a/b/c/iperf3_h1_h2.log
            log_base_name = os.path.basename(input_log)
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                content = f.read()
                visualize_data = self.get_stream_visualize_data(content)
                if not visualize_data:
                    logging.error(f"no visualize data in %s", log_base_name)
                    continue
            log_label = log_base_name.split("_")[0]
            delay = visualize_data.get("delay", None)
            duration = visualize_data.get("duration", None)
            data_array = visualize_data.get("throughput", [])
            if len(data_array) == 0:
                # plot empty data
                data_array = [0] * data_len
            else:
                cur_max_data_value = max(data_array)
                max_data_value = max(max_data_value, cur_max_data_value)
                data_len = max(data_len, len(data_array))
                # for competition flows which have defined the `delay` and `duration`
                # from 0 to `delay` seconds, the throughput is 0
                # from `delay` to `delay + duration` seconds, the throughput is defined in the data_array
                # from `delay + duration` seconds to the end, the throughput is 0
                if delay is not None and duration is not None:
                    delay_seconds = int(delay)
                    duration_seconds = int(duration)
                    tail = max(data_len - delay_seconds - duration_seconds, 1)
                    data_array = [0] * delay_seconds + \
                        data_array + [0] * (tail)
                    protocol = visualize_data.get("protocol", "")
                    cc = visualize_data.get("cc", None)
                    log_label = f"flow({protocol},{cc}): "
                    log_label += visualize_data.get("flow", "")
            logging.debug(f"Added throughput data: %d %s %s",
                          len(data_array), data_array, log_label)
            x = np.arange(0, len(data_array))
            if index < PlotColors.max_value:
                plot_color = PlotColors(index)
                plt.plot(x, data_array[0: len(x)],
                         PlotColorAndMarkerMap[plot_color],
                         markersize=3, linewidth=2, label=f"{log_label}", color=str(plot_color))
            else:
                plt.plot(x, data_array[0: len(x)],
                         '-o',
                         markersize=3, linewidth=2, label=f"{log_label}")
            if max_data_value >= 500:
                plt.ylim(0, max_data_value + 100)
            else:
                plt.ylim(0, max_data_value + 10)
            plt.legend(loc="lower right", fontsize=8)
            index += 1
        if not self.config.output:
            self.config.output = "iperf3_throughput.svg"
        plt.savefig(f"{self.config.output}")
        logging.info("Visualize iperf3 diagram saved to %s",
                     self.config.output)

    def plot_datagram_data(self):
        plt.clf()
        plt.rcParams["font.family"] = "serif"
        # Create 2 subplots in a single column
        fig, axs = plt.subplots(2, 1, figsize=(10, 8))
        fig.suptitle("Iperf3 UDP statistics \n" +
                     self.config.subtitle, fontsize=12, fontweight="bold")
        max_loss_rate = 10  # %
        max_throughput = 0  # Mbps
        data_len = 0
        for input_log in self.config.input:
            if not os.path.exists(input_log):
                continue
            logging.info(f"Visualize iperf3 log: %s", input_log)
            log_base_name = os.path.basename(input_log)
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                content = f.read()
                if 'FlowCompetitionTest' in log_base_name:
                    # FIXME(.): competition flow uses bats.
                    visualize_data = self.get_stream_visualize_data(content)
                else:
                    visualize_data = self.get_datagram_visualize_data(content)
                    if len(visualize_data) == {}:
                        logging.error(
                            f"no visualize data in %s", log_base_name)
                        continue
            delay = visualize_data.get("delay", None)
            duration = visualize_data.get("duration", None)
            log_label = log_base_name.split("_")[0]
            loss_rate_array = visualize_data.get("loss_rate", [])
            cur_max = max(loss_rate_array, default=0)
            max_loss_rate = max(max_loss_rate, cur_max)

            throughput_array = visualize_data.get("throughput", [])
            cur_max = max(throughput_array, default=0)
            max_throughput = max(max_throughput, cur_max)

            data_len = max(data_len, len(throughput_array))
            # for competition flows which have defined the `delay` and `duration`
            if delay is not None and duration is not None:
                delay_seconds = int(delay)
                duration_seconds = int(duration)
                tail = max(data_len - delay_seconds - duration_seconds, 1)
                throughput_array = [0] * delay_seconds + \
                    throughput_array + [0] * (tail)
                protocol = visualize_data.get("protocol", "")
                cc = visualize_data.get("cc", None)
                log_label = f"flow({protocol},{cc}): "
                log_label += visualize_data.get("flow", "")
                loss_rate_array = [0] * data_len

            x = np.arange(1, len(loss_rate_array))
            # Plot loss rate
            axs[0].plot(x, loss_rate_array[0: len(x)], '<--',
                        markersize=4, label=f"{log_label}")
            axs[0].set_title('Loss Rate', fontsize=10)
            axs[0].set_xlabel('Time (s)', fontsize=9)
            axs[0].set_ylabel('Loss Rate (%)', fontsize=9)
            axs[0].legend(loc="upper right", fontsize=8)
            axs[0].grid(True)  # Add grid lines for better readability
            axs[0].set_ylim(-10, max_loss_rate + 10)

            # Plot Jitter rate
            '''
            jitter_array = visualize_data.get("jitter", [])
            x = np.arange(1, len(jitter_array))
            axs[1].plot(x, jitter_array[0: len(x)], 'x-',
                        markersize=4, label=f"{log_label}", color='orange')
            axs[1].set_title('Jitter', fontsize=10)
            axs[1].set_xlabel('Time (s)', fontsize=9)
            axs[1].set_ylabel('Jitter (ms)', fontsize=9)
            axs[1].legend(loc="upper right", fontsize=8)
            axs[1].grid(True)  # Add grid lines for better readability'''

            # Plot throughput
            x = np.arange(0, len(throughput_array))
            axs[1].plot(x, throughput_array[0: len(x)], 'o-',
                        markersize=4, label=f"{log_label}")
            axs[1].set_title('Throughput', fontsize=10)
            axs[1].set_xlabel('Time (s)', fontsize=9)
            axs[1].set_ylabel('Throughput (Mbps)', fontsize=9)
            axs[1].legend(loc="upper right", fontsize=8)
            axs[1].grid(True)  # Add grid lines for better readability
            axs[1].set_ylim(0, max_throughput + 100)
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        if not self.config.output:
            self.config.output = "iperf3_udp_statistics.svg"
        plt.savefig(f"{self.config.output}")
        logging.info("Visualize iperf3 diagram saved to %s",
                     self.config.output)

    def get_stream_visualize_data(self, content):
        visualize_data = {}
        throughput_pattern = r"(\d+) (K|M|G)?Bytes(\s+)(\d+(\.\d+)?) (K|M|G)?bits/sec"
        matches2 = re.findall(throughput_pattern, content)
        throughput_array = [str_to_mbps(
            match[3], match[5]) for match in matches2]
        visualize_data["flow"] = None
        visualize_data["delay"] = None
        visualize_data["duration"] = None
        visualize_data["protocol"] = None
        visualize_data["cc"] = None
        visualize_data["throughput"] = throughput_array
        # delay:10, duration:10, protocol:tcp, cc:bbr
        flow_meta_pattern = r"Competition flow: (.+)?, delay:(\d+)?, duration:(\d+)?, protocol:(.+)?, cc:(.+)?"
        matches = re.findall(flow_meta_pattern, content)
        if matches:
            logging.info(f"flow_meta_pattern: %s", matches)
            visualize_data["flow"] = str(
                matches[0][0]) if matches[0][0] else None
            visualize_data["delay"] = int(
                matches[0][1]) if matches[0][1] else None
            visualize_data["duration"] = int(
                matches[0][2]) if matches[0][2] else None
            visualize_data["protocol"] = str(
                matches[0][3]) if matches[0][3] else None
            visualize_data["cc"] = str(
                matches[0][4]) if matches[0][4] else None
        return visualize_data

    def get_datagram_visualize_data(self, content):
        visualize_data = {}
        matches4 = []
        matches2 = []
        matches3 = []
        throughput_pattern = r"(\d+) (K|M|G)?Bytes(\s+)(\d+(\.\d+)?) (K|M|G)?bits/sec"
        loss_rate_pattern = r"ms(\s+)((-)?\d+/\d+)(\s+)\(((-)?\d+(\.\d+)?)%\)"
        jitter_pattern = r"(K|M|G)?bits/sec(\s+)(\d+(\.\d+)?) ms"
        for line in content.splitlines():
            if line.strip() == "":
                continue
            if "sender" in line or "receiver" in line:
                continue
            matches4.extend(re.findall(loss_rate_pattern, line))
            matches2.extend(re.findall(jitter_pattern, line))
            matches3.extend(re.findall(throughput_pattern, line))
        throughput_array = [str_to_mbps(
            match[3], match[5]) for match in matches3]
        loss_array = [float(match[4]) for match in matches4]
        jitter_array = [float(match[2])
                        for match in matches2]
        visualize_data["loss_rate"] = loss_array
        visualize_data["jitter"] = jitter_array
        visualize_data["throughput"] = throughput_array
        logging.debug(f"loss_rate array: %s", loss_array)
        logging.debug(f"jitter array: %s", jitter_array)
        logging.debug(f"throughput array: %s", throughput_array)
        return visualize_data
