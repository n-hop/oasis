import logging
import time
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite)


class IperfBatsTest(ITestSuite):
    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_iperf(self, client, server, args_from_proto: str):
        if self.config is None:
            logging.error("IperfBatsTest config is None.")
            return False
        receiver_ip = server.IP()
        receiver_port = 5201
        parallel = self.config.parallel or 1
        if parallel > 1:
            logging.info(
                "IperfBatsTest is running with parallel streams: %d", parallel)
        interval_num = self.config.interval_num or 10
        interval = self.config.interval or 1
        for intf in server.getIntfs():
            bats_iperf_server_cmd = f'bats_iperf -s -p {receiver_port} -I {intf}' \
                f' -l {self.result.record} &'
            logging.info(
                'bats_iperf server cmd: %s', bats_iperf_server_cmd)
            server.cmd(f'{bats_iperf_server_cmd}')
        bats_iperf_client_cmd = f'bats_iperf -c {receiver_ip} {args_from_proto} -p {receiver_port} -P {parallel}' \
            f' -i {int(interval)} -t {int(interval_num * interval)}'
        logging.info('bats_iperf client cmd: %s', bats_iperf_client_cmd)
        res = client.popen(
            f'{bats_iperf_client_cmd}').stdout.read().decode('utf-8')
        logging.info('bats_iperf client output: %s', res)
        logging.info('bats_iperf test result save to %s', self.result.record)
        time.sleep(1)
        client.cmd('pkill -9 -f bats_iperf')
        server.cmd('pkill -9 -f bats_iperf')
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
        logging.info(
            "############### Oasis IperfBatsTest from %s to %s ###############", client.name(), server.name())
        return self._run_iperf(client, server, proto_info.get_protocol_args(network))
