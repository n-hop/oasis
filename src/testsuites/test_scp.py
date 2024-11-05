import logging
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo
from .test import (ITestSuite, TestConfig)


class ScpTest(ITestSuite):
    """Measures the time of scp file transfer between two hosts in the network.
    """

    def __init__(self, config: TestConfig) -> None:
        super().__init__(config)
        self.scp_files = []

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
                # 1. Generate scp files
                hosts[i].cmd(
                    f'head -c 30M /dev/urandom > scp_data_30M')
                self.scp_files.append('scp_data_30M')
                # 2. Run scp client
                logging.info(
                    f"############### Oasis ScpTest from "
                    "%s to %s ###############", hosts[i].name(), hosts[0].name())
                scp_cmd = f'scp -i /root/.ssh/id_rsa'
                scp_cmd += f' -o StrictHostKeyChecking=no'
                for file in self.scp_files:
                    scp_cmd += f' {file}'
                scp_cmd += f' root@{receiver_ip}:/tmp/'
                hosts[i].cmd(
                    f'script -c \'{scp_cmd}\' | tee {self.result.record} ')
            return True
        # Run ping test from client to server
        logging.info(
            f"############### Oasis ScpTest from "
            "%s to %s ###############",
            hosts[self.config.client_host].name(),
            hosts[self.config.server_host].name())
        tun_ip = proto_info.get_tun_ip(
            network, self.config.server_host)
        if tun_ip == "":
            tun_ip = hosts[self.config.server_host].IP()
        receiver_ip = tun_ip
        # 1. Generate scp files
        hosts[self.config.client_host].cmd(
            f'head -c 30M /dev/urandom > scp_data_30M')
        self.scp_files.append('scp_data_30M')
        # 2. Run scp client
        scp_cmd = f'scp -o StrictHostKeyChecking=no -i /root/.ssh/id_rsa'
        for file in self.scp_files:
            scp_cmd += f' {file}'
        scp_cmd += f' root@{receiver_ip}:/tmp/'
        scp_res = hosts[self.config.client_host].cmd(
            f'script -c \'{scp_cmd}\' | tee {self.result.record} ')
        logging.info(f"ScpTest result: %s", scp_res)
        return True
