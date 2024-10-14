import logging
import os
import time
import re
from interfaces.network import INetwork
from interfaces.host import IHost
from tools.cfg_generator import generate_cfg_files
from protosuites.proto import (ProtoConfig, IProtoSuite)
from protosuites.proto_info import IProtoInfo
from var.global_var import g_root_path


class BATSProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config: ProtoConfig):
        super().__init__(config)
        if self.config.path is None:
            logging.error("No protocol path specified.")
            return
        self.source_path = '/'.join(self.config.path.split('/')[:-1])
        if self.source_path == '':
            self.source_path = '.'
        else:
            self.source_path = f'{g_root_path}{self.source_path}'
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
        # {g_root_path}src/config/cfg-template/ or {g_root_path}config/cfg-template/
        cfg_template_path = self.config.config_file
        if self.config.config_base_path and self.config.config_file:
            cfg_template_path = os.path.join(
                self.config.config_base_path, self.config.config_file)
        else:
            logging.error("Config base path or config file is not set.")
        logging.debug(
            f"########################## BATSProtocol Source path: %s", self.source_path)
        generate_cfg_files(host_num, hosts_ip_range,
                           self.virtual_ip_prefix, self.source_path, cfg_template_path)
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
        routing_type_name = network.get_routing_strategy().routing_type()
        if routing_type_name == 'OLSRRouting':
            self.protocol_args += " --olsr_adaption_enabled=true"
            self.protocol_args += " --use_netlink_routing_table=true"
            self.protocol_args += " --use_system_link_config=true"
        host_num = len(hosts)
        for i in range(host_num):
            hosts[i].cmd(
                f'nohup {g_root_path}{self.config.path} {self.protocol_args} '
                f' > {self.log_dir}bats_protocol_h{i}.log &')

        # check the protocol is running
        max_sleep_time = host_num
        running_flag = "bats_uds_socket_bind_point."
        host_range = list(range(host_num))
        while max_sleep_time > 0 and len(host_range) > 0:
            max_sleep_time -= 1
            time.sleep(1)
            unready_idx = []
            for host_idx in host_range:
                # /tmp/bats_uds_socket_bind_point.xxx
                res = hosts[host_idx].cmd(f'ls /tmp | grep "{running_flag}"')
                if res.find(running_flag) == -1:
                    unready_idx.append(host_idx)
            host_range = unready_idx

        if len(host_range) > 0:
            failed_hosts = ""
            for idx in host_range:
                failed_hosts += f"{hosts[idx].name()} "
            logging.error(
                f"############### Oasis run bats protocol failed on "
                "%s ###############", failed_hosts)
            return False

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
                f'pkill -9 -f {self.process_name}')
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
            f'cp {self.source_path}/h{host_idx}.ini /etc/bats-protocol/bats-protocol-settings.ini')
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

    def get_protocol_name(self) -> str:
        # name can be 'btp' or 'btp_xxx_feature'
        return self.config.name.replace('_', '-').upper()
