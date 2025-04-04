from typing import List, Dict, Any
import threading
import time
import logging
import argparse
import psutil


class PsutilNetworkMonitor():
    """Network monitor implementation using psutil"""

    def __init__(self):
        self.interfaces = []
        self.interval = 1.0
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        self.results = []
        self.is_monitoring = False
        self.average_tx_throughput = 0.0
        self.average_rx_throughput = 0.0

    def start_monitoring(self, interfaces: List[str], interval: float = 1.0) -> None:
        """Start monitoring the specified network interfaces"""
        if self.is_monitoring:
            logging.warning(
                "Network monitoring is already running. Stopping previous session.")
            self.stop_monitoring()
        all_interfaces = psutil.net_if_addrs()
        if not interfaces:
            logging.error("No network interfaces specified for monitoring")
            return
        for iface in all_interfaces:
            logging.info(
                "========> Available Interface %s ", iface)

        self.interfaces = interfaces
        self.interval = interval
        self.results = []
        self.stop_event.clear()

        self.monitoring_thread = threading.Thread(target=self._monitor_network)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        self.is_monitoring = True
        logging.info(
            "Started monitoring interfaces: %s", ', '.join(self.interfaces))

    def stop_monitoring(self) -> None:
        """Stop monitoring network interfaces"""
        if not self.is_monitoring:
            return

        self.stop_event.set()
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
        self.is_monitoring = False
        logging.info("Network monitoring stopped")

    def get_results(self) -> Dict[str, Any]:
        """Get the monitoring results"""
        return {
            "interfaces": self.interfaces,
            "interval": self.interval,
            "measurements": self.results
        }

    def write_results_to_file(self, filename: str) -> None:
        """Write monitoring results to a file"""
        with open(filename, 'a', encoding='utf-8') as f:
            f.write("\n=== Network Throughput Results ===\n")
            f.write("Timestamp,Interface,Bytes Sent (MB/s),Bytes Received (MB/s)\n")
            f.write(
                f"Average TX Throughput: {self.average_tx_throughput:.3f} MB/s\n")
            f.write(
                f"Average RX Throughput: {self.average_rx_throughput:.3f} MB/s\n")
            for entry in self.results:
                f.write(
                    f"{entry['timestamp']},{entry['interface']},{entry['bytes_sent']:.3f},{entry['bytes_recv']:.3f}\n")

    def _monitor_network(self) -> None:
        """Internal method to monitor network traffic"""
        previous_counters = psutil.net_io_counters(pernic=True)

        while not self.stop_event.is_set():
            time.sleep(self.interval)
            try:
                current_counters = psutil.net_io_counters(pernic=True)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                for iface in self.interfaces:
                    if iface in previous_counters and iface in current_counters:
                        bytes_sent = (current_counters[iface].bytes_sent -
                                      previous_counters[iface].bytes_sent) / self.interval / (1024 * 1024)
                        bytes_recv = (current_counters[iface].bytes_recv -
                                      previous_counters[iface].bytes_recv) / self.interval / (1024 * 1024)
                        self.average_tx_throughput = (
                            self.average_tx_throughput + bytes_sent) / 2
                        self.average_rx_throughput = (
                            self.average_rx_throughput + bytes_recv) / 2
                        # Store results
                        self.results.append({
                            "timestamp": timestamp,
                            "interface": iface,
                            "bytes_sent": bytes_sent,
                            "bytes_recv": bytes_recv
                        })
                        logging.info(
                            "Interface %s: Send: %.3f MB/s, Receive: %.3f MB/s", iface, bytes_sent, bytes_recv)
                previous_counters = current_counters
            except Exception as e:
                logging.error("Error monitoring network: %s", e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='Monitor network throughput using psutil')
    parser.add_argument(
        '--interfaces', nargs='+', required=True,
        help='List of network interfaces to monitor')
    parser.add_argument(
        '--interval', type=float, default=1.0,
        help='Interval in seconds for monitoring (default: 1.0)')
    parser.add_argument(
        '--monitoring_time', type=int, default=10,
        help='Time in seconds to monitor (default: 10)')
    parser.add_argument(
        '--output', type=str, default='network_monitoring_results.csv',
        help='Output file name for monitoring results (default: network_monitoring_results.csv)')
    monitor = PsutilNetworkMonitor()
    monitor.start_monitoring(
        interfaces=parser.parse_args().interfaces,
        interval=parser.parse_args().interval)
    logging.info("Monitoring started on interfaces: %s",
                 monitor.interfaces)
    time.sleep(parser.parse_args().monitoring_time)
    monitor.stop_monitoring()
    results = monitor.get_results()
    monitor.write_results_to_file(parser.parse_args().output)
    logging.info("Monitoring results saved to %s", parser.parse_args().output)
