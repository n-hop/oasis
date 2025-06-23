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
        if self.config.client_host is None or self.config.server_host is None:
            logging.error(
                "Only support scp test with client and server hosts.")
            return False
        hosts_num = len(hosts)
        if self.config.client_host >= hosts_num or self.config.server_host >= hosts_num:
            logging.error(
                "Client or server host index is out of range: %d, %d", self.config.client_host, self.config.server_host)
            return False
        receiver_ip = None
        target_file_name = f'scp_data_{self.config.file_size}M'
        gen_file_cmd = f'head -c {self.config.file_size}M /dev/urandom > {target_file_name}'
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
        hosts[self.config.client_host].cmd(f'{gen_file_cmd}')
        self.scp_files.append(f'{target_file_name}')
        # 2. Run scp client
        scp_cmd = f'scp -o StrictHostKeyChecking=no -i /root/.ssh/id_rsa'
        for file in self.scp_files:
            scp_cmd += f' {file}'
        scp_cmd += f' root@{receiver_ip}:/tmp/'
        scp_res = hosts[self.config.client_host].cmd(
            f'script -c \'{scp_cmd}\' | tee {self.result.record} ')
        logging.info(f"ScpTest result: %s", scp_res)
        with open(self.result.record, 'a', encoding='utf-8') as f:
            for file in self.scp_files:
                org_file_hash = self.__get_file_hash(
                    hosts[self.config.client_host], file)
                received_file_hash = self.__get_file_hash(
                    hosts[self.config.server_host], f'/tmp/{file}')
                if org_file_hash != "ERROR" and org_file_hash == received_file_hash:
                    f.write(f"{file}: passed\n")
                else:
                    logging.warning(
                        "File %s hash mismatch: original %s, received %s",
                        file, org_file_hash, received_file_hash)
                    f.write(f"{file}: failed\n")
        return True

    def __get_file_hash(self, host, file):
        """Get the hash of the scp files."""
        popen_res = host.popen(
            f'sha256sum {file}')
        if popen_res and hasattr(popen_res, "stdout"):
            output = popen_res.stdout.read().decode('utf-8')
            logging.info(f"ScpTest __get_file_hash output: %s", output)
            file_hash = output.split()[0] if output else "ERROR"
        else:
            file_hash = "ERROR"
            logging.error(
                "Failed to get hash for file %s, using ERROR as placeholder.", {file})
        return file_hash
