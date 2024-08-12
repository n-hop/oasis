import logging
import time
from interfaces.network import INetwork
from interfaces.host import IHost
from tools.cfg_generator import generate_cfg_files
from protosuites.proto import (ProtoConfig, IProtoSuite)
from protosuites.proto_info import IProtoInfo


class BATSProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config: ProtoConfig):
        super().__init__(config)
        if self.config.protocol_path is None or self.config.hosts is None:
            logging.error("No protocol path or hosts set")
        self.process_name = self.config.protocol_path.split('/')[-1]
        self.source_path = '/'.join(self.config.protocol_path.split('/')[:-1])
        if self.source_path == '':
            self.source_path = '.'

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        # Init the license file for bats, otherwise it will not run.
        hosts = network.get_hosts()
        host_num = len(hosts)
        # prepare the bats protocol config files
        hosts_ip_range = network.get_host_ip_range()
        generate_cfg_files(host_num, hosts_ip_range, self.source_path)
        for i in range(host_num):
            self._init_tun(hosts[i])
            self._init_config(hosts[i])
            logging.info(
                f"############### Oasis install bats protocol config files on "
                "%s ###############",
                hosts[i].name())
        return True

    def run(self, network: INetwork):
        hosts = network.get_hosts()
        host_num = len(hosts)
        for i in range(host_num):
            res = hosts[i].cmd(
                f'{self.config.protocol_path} {self.config.protocol_args} '
                f' ')
            logging.info(
                f"############### Oasis run bats protocol on "
                "%s, %s ###############",
                hosts[i].name(), res)
        time.sleep(2)
        return True

    def stop(self, network: INetwork):
        hosts = network.get_hosts()
        host_num = len(hosts)
        for i in range(host_num):
            logging.info(
                f"############### Oasis stop bats protocol on "
                "%s ###############",
                hosts[i].name())
            hosts[i].cmd(
                f'pkill -f {self.process_name}')
        return True

    def _init_tun(self, host: IHost):
        host.cmd(f'mkdir /dev/net')
        host.cmd(f'mknod /dev/net/tun c 10 200')
        host.cmd(f'ip tuntap add mode tap tap')
        return True

    def _init_config(self, host: IHost):
        # {host.name()} = h0, h1, h2, ... the last character is the index of the host
        host_idx = int(host.name()[-1])
        host.cmd(
            f'mkdir -p /etc/cfg')
        host.cmd(
            f'cp {self.source_path}/licence /etc/cfg/')
        host.cmd(
            f'mkdir -p /etc/bats-protocol')
        host.cmd(
            f'mv {self.source_path}/h{host_idx}.ini /etc/bats-protocol/bats-protocol-settings.ini')
        return True

    def get_forward_port(self) -> int:
        pass

    def get_tun_ip(self) -> str:
        pass
