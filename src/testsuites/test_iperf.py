import logging
import time
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite, TestConfig)


class IperfTest(ITestSuite):
    def __init__(self, config: TestConfig) -> None:
        super().__init__(config)
        self.is_udp_mode = False
        if self.config.packet_type == "udp":
            self.is_udp_mode = True
            if self.config.bitrate == 0:
                self.config.bitrate = 1
            logging.info("IperfTest is in UDP mode, bitrate: %d Mbps",
                         self.config.bitrate)

    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_iperf(self, client, server, recv_port, recv_ip):
        if self.config is None:
            logging.error("IperfTest config is None.")
            return False
        interval_num = self.config.interval_num or 10
        interval = self.config.interval or 1
        server.cmd(f'iperf3 -s -p {recv_port} -i {int(interval)} -V --forceflush'
                   f' --logfile {self.result.record} &')
        iperf3_client_cmd = f'iperf3 -c {recv_ip} -p {recv_port} -i {int(interval)}' \
            f' -t {int(interval_num * interval)}'
        if self.is_udp_mode:
            iperf3_client_cmd += f' -u -b {self.config.bitrate}M'
        else:
            iperf3_client_cmd += f' --connect-timeout 5000'
            if self.config.bitrate != 0:
                iperf3_client_cmd += f' -b {self.config.bitrate}M'
        logging.info('iperf client cmd: %s', iperf3_client_cmd)
        res = client.popen(
            f'{iperf3_client_cmd}').stdout.read().decode('utf-8')
        logging.info('iperf client output: %s', res)
        logging.info('iperf test result save to %s', self.result.record)
        time.sleep(1)
        client.cmd('pkill -9 -f iperf3')
        server.cmd('pkill -9 -f iperf3')
        return True

    def _run_test(self, network: INetwork, proto_info: IProtoInfo):
        hosts = network.get_hosts()
        if hosts is None:
            return False
        if self.config.client_host is None or self.config.server_host is None:
            self.config.client_host = 0
            self.config.server_host = len(hosts) - 1

        client = hosts[self.config.client_host]
        server = hosts[self.config.server_host]
        receiver_ip = None
        if (proto_info.get_protocol_name().upper() == "KCP") or (proto_info.get_protocol_name().upper() == "QUIC"):
            # kcp tun like a proxy, all traffic will be forwarded to the proxy server
            tun_ip = proto_info.get_tun_ip(network, self.config.client_host)
            if tun_ip == "":
                tun_ip = client.IP()
            receiver_ip = tun_ip
        else:
            tun_ip = proto_info.get_tun_ip(network, self.config.server_host)
            if tun_ip == "":
                tun_ip = server.IP()
            receiver_ip = tun_ip
        # only kcp has forward port `10100`
        receiver_port = proto_info.get_forward_port()
        if receiver_port == 0:
            # if no forward port defined, use iperf3 default port 5201
            receiver_port = 5201
        logging.info(
            "############### Oasis IperfTest from %s to %s ###############", client.name(), server.name())
        return self._run_iperf(client, server, receiver_port, receiver_ip)
