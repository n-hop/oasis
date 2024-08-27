import logging
import os
import time
import re
from interfaces.network import INetwork
from interfaces.host import IHost
from tools.cfg_generator import generate_cfg_files
from protosuites.proto import (ProtoConfig, IProtoSuite)
from protosuites.proto_info import IProtoInfo


class BATSProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config: ProtoConfig):
        super().__init__(config)
        if self.config.path is None:
            logging.error("No protocol path specified.")
            return
        self.process_name = self.config.path.split('/')[-1]
        self.source_path = '/'.join(self.config.path.split('/')[:-1])
        if self.source_path == '':
            self.source_path = '.'
        self.virtual_ip_prefix = '1.0.0.'
        self.license_path = f'{self.source_path}/licence'

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        # Init the license file for bats, otherwise it will not run.
        hosts = network.get_hosts()
        if hosts is None:
            return False
        host_num = len(hosts)
        # prepare the bats protocol config files
        hosts_ip_range = network.get_host_ip_range()
        if hosts_ip_range == "":
            logging.error("Hosts ip range is not set.")
            return False
        generate_cfg_files(host_num, hosts_ip_range,
                           self.virtual_ip_prefix, self.source_path)
        # generate some error log if the license file is not correct
        self._verify_license()
        for i in range(host_num):
            hosts[i].cmd(f'iptables -F -t nat')
            self._init_tun(hosts[i])
            self._init_config(hosts[i])
            logging.info(
                f"############### Oasis install bats protocol config files on "
                "%s ###############",
                hosts[i].name())
        return True

    def run(self, network: INetwork):
        hosts = network.get_hosts()
        if hosts is None:
            return False
        host_num = len(hosts)
        for i in range(host_num):
            hosts[i].cmd(
                f'{self.config.path} {self.protocol_args} '
                f' > {self.log_dir}bats_protocol_h{i}.log &')
            logging.info(
                f"############### Oasis run bats protocol on "
                "%s ###############",
                hosts[i].name())
        time.sleep(2)
        return True

    def stop(self, network: INetwork):
        hosts = network.get_hosts()
        if hosts is None:
            return False
        host_num = len(hosts)
        for i in range(host_num):
            logging.info(
                f"############### Oasis stop bats protocol on "
                "%s ###############",
                hosts[i].name())
            hosts[i].cmd(
                f'pkill -f {self.process_name}')
            hosts[i].cmd(f'ip tuntap del mode tap tap')
            hosts[i].cmd(f'iptables -F -t nat')
        return True

    def _init_tun(self, host: IHost):
        host.cmd(f'mkdir /dev/net')
        host.cmd(f'mknod /dev/net/tun c 10 200')
        host.cmd(f'ip tuntap add mode tap tap')
        return True

    def _verify_license(self) -> bool:
        if not self.license_path:
            logging.error(
                "############### License file path is not set ###############")
            return False
        if not os.path.exists(self.license_path):
            logging.error(
                "############### License file not found ###############")
            return False
        with open(self.license_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.find('Hardware_info') == -1 or content.find('Licence_id') == -1:
                logging.error(
                    "############### Missing License id in file ###############")
                return False
        return True

    def _init_config(self, host: IHost):
        # {host.name()} = h0, h1, h2, ... the last character is the index of the host
        host_idx = int(host.name()[-1])
        host.cmd(
            f'mkdir -p /etc/cfg')
        host.cmd(
            f'cp {self.license_path} /etc/cfg/')
        host.cmd(
            f'mkdir -p /etc/bats-protocol')
        host.cmd(
            f'mv {self.source_path}/h{host_idx}.ini /etc/bats-protocol/bats-protocol-settings.ini')
        return True

    def _get_ip_from_host(self, host: IHost, dev: str) -> str:
        pf = host.popen(f"ip addr show {dev}")
        if pf is None:
            return ""
        ip = pf.stdout.read().decode('utf-8')
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip)
        if match:
            return match.group(1)
        return ""

    def get_forward_port(self) -> int:
        return 0

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        return ""

    def get_protocol_version(self) -> str:
        return str(self.config.version)
