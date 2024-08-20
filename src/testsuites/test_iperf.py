import logging
import time
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite)


class IperfTest(ITestSuite):

    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_iperf(self, client, server, recv_port, recv_ip, version):
        server.cmd(f'iperf3 -s -p {recv_port} -i {int(self.config.interval)} -V --forceflush'
                   f' --logfile {self.result.record} &')
        iperf3_client_cmd = f'iperf3 -c {recv_ip} -p {recv_port} -i {int(self.config.interval)}' \
                            f' -t {int(self.config.interval_num * self.config.interval)}'
        if version is not None and version != "":
            iperf3_client_cmd += f' --congestion {version}'
        res = client.popen(
            f'{iperf3_client_cmd}').stdout.read().decode('utf-8')
        logging.info('iperf client output: %s', res)
        logging.info('iperf test result save to %s', self.result.record)
        time.sleep(1)
        client.cmd('pkill -f iperf3')
        server.cmd('pkill -f iperf3')
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
        receiver_port = proto.get_forward_port(
            network, self.config.server_host)
        if receiver_port is None:
            receiver_port = 5201
        logging.info(
            "############### Oasis IperfTest from %s to %s ###############", client.name(), server.name())
        protocol_version = ""
        if proto.get_protocol_name() == "TCP":
            protocol_version = proto.get_protocol_version()
            logging.info(
                "############### Oasis IperfTest protocol version %s ###############", protocol_version)
        return self._run_iperf(client, server, receiver_port, receiver_ip, protocol_version)
