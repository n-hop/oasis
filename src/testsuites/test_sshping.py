import logging
import os
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from var.global_var import g_root_path
from .test import (ITestSuite, TestConfig)


class SSHPingTest(ITestSuite):
    """Measures the RTT of ssh ping message between two hosts in the network.
       SSHPingTest https://github.com/spook/sshping
    """

    def __init__(self, config: TestConfig) -> None:
        super().__init__(config)
        self.binary_path = f"{g_root_path}bin/ssh/sshping"
        if not os.path.isfile(f"{self.binary_path}"):
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
        receiver_ip = None
        if self.config.client_host is None or self.config.server_host is None:
            for i in range(hosts_num):
                if i == 0:
                    continue
                tun_ip = proto_info.get_tun_ip(
                    network, 0)
                if tun_ip == "":
                    tun_ip = hosts[0].IP()
                receiver_ip = tun_ip
                logging.info(
                    f"############### Oasis SSHPingTest from "
                    "%s to %s ###############", hosts[i].name(), hosts[0].name())
                hosts[i].cmd(
                    f'{self.binary_path} -i /root/.ssh/id_rsa'
                    f' -H root@{receiver_ip} > {self.result.record}')
            return True
        # Run ping test from client to server
        logging.info(
            f"############### Oasis SSHPingTest from "
            "%s to %s ###############",
            hosts[self.config.client_host].name(),
            hosts[self.config.server_host].name())
        tun_ip = proto_info.get_tun_ip(
            network, self.config.server_host)
        if tun_ip == "":
            tun_ip = hosts[self.config.server_host].IP()
        receiver_ip = tun_ip
        hosts[self.config.client_host].cmd(
            f'{self.binary_path} -i /root/.ssh/id_rsa'
            f' -H root@{receiver_ip} > {self.result.record}')
        return True
