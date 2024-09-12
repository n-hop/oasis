import logging
import re
import os
import matplotlib.pyplot as plt
import numpy as np
from .analyzer import IDataAnalyzer


class SSHPingAnalyzer(IDataAnalyzer):
    """Analyze and visualize multiple input sshping logs.
    """

    def analyze(self):
        return True

    def visualize(self):
        """
        plot sshping graph
        """
        data_sshping_all = {}
        plt.clf()
        plt.rcParams['font.family'] = 'serif'
        plt.xlabel('Time (ms)', fontsize=8,
                   fontweight='bold')
        plt.ylabel('RTT (ms)', fontsize=8,
                   fontweight='bold')
        default_title = "SSHPing RTT for each packet\n"
        default_title += self.config.subtitle
        plt.title(default_title, fontsize=10, fontweight="bold")
        sshping_pattern = r"Ping (\d+)/1000:\s+([\d.]+) ms"
        total_pings = 1000
        is_plot = False
        for input_log in self.config.input:
            logging.info(f"Visualize rtt log: %s", input_log)
            if not os.path.exists(input_log):
                logging.error("sshping log file %s not found", input_log)
                continue
            log_base_name = os.path.basename(input_log)
            data_sshping_all[log_base_name] = []
            with open(f"{input_log}", "r", encoding='utf-8') as f:
                content = f.read()
                pings = {}
                for match in re.findall(sshping_pattern, content):
                    ping_id = int(match[0])
                    rtt = float(match[1])
                    pings[ping_id] = rtt
                rtt_values = [pings.get(i, None)
                              for i in range(total_pings)]
                x_values = list(range(total_pings))
                valid_x = [x for x, y in zip(
                    x_values, rtt_values) if y is not None]
                valid_y = [y for y in rtt_values if y is not None]
                data_sshping_all[log_base_name] = valid_y
                # start plot x-y scatter graph: x is time in ms,
                log_label = log_base_name.split("_")[0]
                plt.scatter(valid_x, valid_y,
                            s=3, alpha=0.5, label=f"{log_label}")
                plt.legend(loc='upper left', fontsize=8)
                is_plot = True
        if not is_plot:
            logging.warning("no data to plot")
            return
        if not self.config.output:
            self.config.output = "sshping.svg"
        if '.svg' not in self.config.output:
            plt.savefig(f"{self.config.output}sshping.svg")
            logging.info("Visualize sshping diagram saved to %s",
                         self.config.output)
        else:
            plt.savefig(f"{self.config.output}")
            logging.info("Visualize sshping diagram saved to %s",
                         self.config.output)
        self.plot_sshping_cdf(data_sshping_all)

    def plot_sshping_cdf(self, rtt_data: dict):
        plt.clf()
        plt.rcParams['font.family'] = 'serif'
        plt.xlabel('RTT (ms)', fontsize=8,
                   fontweight='bold')
        plt.ylabel('Cumulative Probability', fontsize=8,
                   fontweight='bold')
        default_title = "SSHPing CDF\n"
        default_title += self.config.subtitle
        plt.title(default_title, fontsize=10, fontweight="bold")
        for log_base_name, rtt_list in rtt_data.items():
            if len(rtt_list) == 0:
                logging.warning(
                    f"no per sshping data in %s", log_base_name)
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
            plt.savefig(f"{self.config.output}sshping_cdf.svg")
            logging.info("Visualize sshping CDF diagram saved to %s",
                         self.config.output)
        else:
            path = os.path.dirname(self.config.output)
            plt.savefig(f"{path}sshping_cdf.svg")
            logging.info("Visualize sshping CDF diagram saved to %s",
                         path)
