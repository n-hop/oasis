import time
import logging

from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite, TestConfig)


class RTTTest(ITestSuite):
    """Measures the round trip time between two hosts in the network.
       RTTTest uses tool `bin/tcp_message/tcp_endpoint` to measure the RTT.
       Source of the tool is in https://github.com/n-hop/bats-documentation
    """

    def __init__(self, config: TestConfig) -> None:
        super().__init__(config)
        self.run_times = 0
        self.first_rtt_repeats = 15

    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_tcp_endpoint(self, client, server, port, recv_ip):
        loop_cnt = 1
        server.cmd(f'/root/bin/tcp_message/tcp_endpoint -p {port} &')
        tcp_client_cmd = f'/root/bin/tcp_message/tcp_endpoint -c {recv_ip} -p {port}'
        tcp_client_cmd += f' -i {self.config.interval}' \
            f' -w {self.config.packet_count} -l {self.config.packet_size}'
        if self.config.packet_count == 1:
            # measure the first rtt, repeat 10 times
            loop_cnt = self.first_rtt_repeats
            tcp_client_cmd += f' >> {self.result.record}'
        else:
            tcp_client_cmd += f' > {self.result.record}'
        for _ in range(loop_cnt):
            client.cmd(f'{tcp_client_cmd}')
            client.cmd('pkill -f tcp_endpoint')
        logging.info('rtt test result save to %s', self.result.record)
        time.sleep(1)
        server.cmd('pkill -f tcp_endpoint')
        return True

    def _run_test(self, network: INetwork, proto: IProtoInfo):
        hosts = network.get_hosts()

        if self.config.client_host is None or self.config.server_host is None:
            self.config.client_host = 0
            self.config.server_host = len(hosts) - 1

        client = hosts[self.config.client_host]
        server = hosts[self.config.server_host]
        receiver_ip = None
        if proto.get_protocol_name().upper() == "KCP":
            # kcp tun like a proxy, all traffic will be forwarded to the proxy server
            tun_ip = proto.get_tun_ip(network, self.config.client_host)
            if tun_ip is None or tun_ip == "":
                tun_ip = client.IP()
            receiver_ip = tun_ip
        else:
            tun_ip = proto.get_tun_ip(network, self.config.server_host)
            if tun_ip is None or tun_ip == "":
                tun_ip = server.IP()
            receiver_ip = tun_ip
        # KCP defines the forward port
        receiver_port = proto.get_forward_port()
        if receiver_port is None:
            # for port conflict, use different port for each test
            receiver_port = 10011 + self.run_times
            self.run_times += 1
        logging.info(
            "############### Oasis RTTTest from %s to %s with forward port %s ###############",
            client.name(), server.name(), receiver_port)
        return self._run_tcp_endpoint(client, server, receiver_port, receiver_ip)
