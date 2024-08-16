import logging

from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite)


class PingTest(ITestSuite):
    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_test(self, network: INetwork, proto: IProtoInfo):
        hosts = network.get_hosts()
        hosts_num = len(hosts)
        if self.config.client_host is None or self.config.server_host is None:
            for i in range(hosts_num):
                if i == 0:
                    continue
                logging.info(
                    f"############### Oasis PingTest from "
                    "%s to %s ###############", hosts[i].name(), hosts[0].name())
                res = hosts[i].cmd(f'ping -c 5 -W 1 -i 0.1 '
                                   f'{hosts[0].IP()}'
                                   f' > {self.result.record}')
                logging.info('host %s', res)
                if "100% packet loss" in res:
                    logging.error("Ping test failed")
                    return False
            return True
        # Run ping test from client to server
        logging.info(
            f"############### Oasis PingTest from "
            "%s to %s ###############",
            hosts[self.config.client_host].name(),
            hosts[self.config.server_host].name())
        res = hosts[self.config.client_host].popen(
            f'ping -c 100 -W 1 -i 0.01 '
            f'{hosts[self.config.server_host].IP()}').stdout.read().decode('utf-8')
        logging.info('host %s', res)
        if "100% packet loss" in res:
            logging.error("Ping test failed")
            return False
        return True
