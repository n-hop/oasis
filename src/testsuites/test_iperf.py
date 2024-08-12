import logging
import time
from interfaces.network import INetwork
from data_analyzer.analyzer import AnalyzerConfig
from data_analyzer.analyzer_factory import AnalyzerFactory
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite)


class IperfTest(ITestSuite):

    def post_process(self):
        analyzer = AnalyzerFactory.get_analyzer("iperf3")
        config = AnalyzerConfig(
            input=self.config.log_file, output="iperf3_result.svg")
        config.input = self.config.log_file
        config.output = "iperf3_result.svg"
        analyzer.analyze(config)
        analyzer.visualize(config)
        return True

    def pre_process(self):
        self.config.log_file = "iperf3_log.txt"
        return True

    def _run_iperf(self, client, server, recv_port, recv_ip):
        server.cmd(f'nohup iperf3 -s -p {recv_port} -i {int(self.config.interval)} -V --forceflush'
                   f' --logfile {self.config.log_file} &')
        client.cmd(f'iperf3 -c {recv_ip} -p {recv_port} -i {int(self.config.interval)}'
                   f' -t {int(self.config.interval_num * self.config.interval)}')
        time.sleep(1)
        client.cmd('pkill -f iperf3')
        server.cmd('pkill -f iperf3')

    def _run_test(self, network: INetwork, proto: IProtoInfo):
        logging.info(
            "############### Oasis IperfTest ###########")
        hosts = network.get_hosts()
        client =  hosts[0]
        server = hosts[-1]
        receiver_ip = proto.get_tun_ip(network, len(hosts) - 1)
        if receiver_ip is None:
            receiver_ip = server.IP()
        receiver_port = proto.get_forward_port(network, len(hosts) - 1)
        if receiver_port is None:
            receiver_port = 5201

        self._run_iperf(client, server, receiver_port, receiver_ip)
