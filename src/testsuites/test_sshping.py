import logging
import os
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite, TestConfig)


class SSHPingTest(ITestSuite):
    """Measures the RTT of ssh ping message between two hosts in the network.
       SSHPingTest https://github.com/spook/sshping
    """

    def __init__(self, config: TestConfig) -> None:
        super().__init__(config)
        self.binary_path = "bin/ssh/sshping"
        if not os.path.isfile(f"/root/{self.binary_path}"):
            logging.error("test tool binary %s is not found.",
                          self.binary_path)

    def post_process(self):
        return True

    def pre_process(self):
        return True

    def _run_test(self, network: INetwork, proto_info: IProtoInfo):
        hosts = network.get_hosts()
        if hosts is None:
            logging.error("No host found in the network")
            return False
        hosts_num = len(hosts)
        if self.config.client_host is None or self.config.server_host is None:
            for i in range(hosts_num):
                if i == 0:
                    continue
                logging.info(
                    f"############### Oasis SSHPingTest from "
                    "%s to %s ###############", hosts[i].name(), hosts[0].name())
                hosts[i].cmd(
                    f'{self.binary_path} -i / root/.ssh/id_rsa'
                    f' --connect-time 5 -t 8 root@{hosts[0].IP()} > {self.result.record}')
            return True
        # Run ping test from client to server
        logging.info(
            f"############### Oasis SSHPingTest from "
            "%s to %s ###############",
            hosts[self.config.client_host].name(),
            hosts[self.config.server_host].name())
        hosts[self.config.client_host].cmd(
            f'{self.binary_path} -i /root/.ssh/id_rsa'
            f' --connect-time 5 -t 8 root@{hosts[self.config.server_host].IP()} > {self.result.record}')
        return True
