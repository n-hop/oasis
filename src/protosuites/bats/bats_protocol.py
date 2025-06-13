import logging
import os
import time
import re

from interfaces.network import INetwork
from interfaces.host import IHost
from protosuites.proto import (ProtoConfig, IProtoSuite, ProtoRole)
from tools.cfg_generator import generate_cfg_files, generate_olsr_cfg_files


class BATSProtocol(IProtoSuite):
    def __init__(self, config: ProtoConfig, is_distributed: bool = True, role: ProtoRole = ProtoRole.both):
        super().__init__(config, is_distributed, role)
        logging.info("#### BATSProtocol config %s",
                     self.config)
        self.protocol_args: str
        if self.config.bin is None:
            logging.error("No protocol binary specified.")
            return
        self.virtual_ip_prefix = '1.0.0.'
        self.license_path = None

    def is_distributed(self) -> bool:
        return self.is_distributed_var

    def post_run(self, network: INetwork):
        return True

    def is_ready_on(self, host: IHost) -> bool:
        pf = host.popen(
            f"bats_cli api main_node")
        if pf is None:
            logging.error("Failed to run bats_cli on %s", host.name())
            return False
        output = pf.stdout.read().decode('utf-8')
        match = re.search(r'state: started', output)
        if match:
            logging.info("Bats protocol is ready on %s %s",
                         host.name(), output)
            return True
        logging.debug("Bats protocol is not ready on %s,%s",
                      host.name(), output)
        return False

    def pre_run(self, network: INetwork):
        # Init the license file for bats, otherwise it will not run.
        all_hosts = network.get_hosts()
        if all_hosts is None:
            logging.error("No host found in the network")
            return False

        if not self.is_distributed_var:
            if self.config.hosts is None or len(self.config.hosts) != 1:
                logging.error(
                    "Test non-distributed protocols, but bats protocol server/client hosts are not set correctly.")
                return False
        net_id = network.get_id()
        all_hosts_num = len(all_hosts)
        if self.is_distributed_var:
            self.config.hosts = list(range(all_hosts_num))
            logging.info(
                "############### Oasis start bats protocol on all hosts %d###############",
                all_hosts_num)
        else:
            logging.info(
                "############### Oasis start bats protocol on specified hosts %d ###############",
                len(self.config.hosts) if self.config.hosts is not None else 0)
        if self.config.hosts is None:
            logging.error(
                "config.hosts is None, unable to start the protocol.")
            return False
        # prepare the bats protocol config files
        hosts_ip_range = network.get_host_ip_range()
        if hosts_ip_range == "":
            logging.error("Hosts ip range is not set.")
            return False
        # {g_root_path}src/config/cfg-template/ or {g_root_path}config/cfg-template/
        cfg_template_path = self.config.config_file
        if self.config.config_base_path is None:
            logging.error(
                "Config base path or config file is not set.")
        if self.config.config_base_path and self.config.config_file:
            cfg_template_path = os.path.join(
                self.config.config_base_path, self.config.config_file)
        # configurations are separated by network
        extend_path = ""
        if not self.is_distributed_var and self.proto_role == ProtoRole.client:
            extend_path = 'client'
        elif not self.is_distributed_var and self.proto_role == ProtoRole.server:
            extend_path = 'server'
        else:
            extend_path = f'{net_id}'
        routing_type_name = network.get_routing_strategy().routing_type()
        if routing_type_name == 'OLSRRouting':
            self.virtual_ip_prefix = '172.23.1.'
            generate_olsr_cfg_files(
                all_hosts_num, self.virtual_ip_prefix, f'{self.log_config_dir}{extend_path}')
        else:
            test_tun_mode = 'BRTP' if self.get_protocol_name() == 'BRTP' else 'BTP'
            generate_cfg_files(all_hosts_num, hosts_ip_range,
                               self.virtual_ip_prefix, f'{self.log_config_dir}{extend_path}',
                               test_tun_mode,
                               cfg_template_path)
        # generate some error log if the license file is not correct
        self._verify_license()
        for i in self.config.hosts:
            all_hosts[i].cmd(f'iptables -F -t nat')
            self._init_tun(all_hosts[i])
            self._init_config(all_hosts[i], net_id)
        return True

    def run(self, network: INetwork):
        if self.config.hosts is None:
            logging.error(
                "config.hosts is None, unable to start the protocol.")
            return False
        all_hosts = network.get_hosts()
        if all_hosts is None:
            logging.error("No host found in the network")
            return False
        routing_type_name = network.get_routing_strategy().routing_type()
        if routing_type_name == 'OLSRRouting':
            self.protocol_args += " --olsr_adaption_enabled=true"
            self.protocol_args += " --use_netlink_routing_table=true"
            self.protocol_args += " --use_user_routing_table=false"
            self.protocol_args += " --use_system_link_config=true"
            self.protocol_args += " --use_user_link_config=false"
        selected_host_num = len(self.config.hosts)
        logging.info(
            f"############### Oasis start bats protocol on %s ###############",
            selected_host_num)
        for i in self.config.hosts:
            all_hosts[i].cmd(
                f'nohup {self.config.bin} {self.protocol_args} '
                f' > {self.log_dir}bats_protocol_h{i}.log &')

        # check the protocol is running
        max_sleep_time = selected_host_num + 1
        not_ready_host_range = list(range(selected_host_num))
        while max_sleep_time > 0 and len(not_ready_host_range) > 0:
            max_sleep_time -= 1
            time.sleep(1)
            cur_not_ready_idx = []
            for host_idx in not_ready_host_range:
                if not self.is_ready_on(all_hosts[host_idx]):
                    cur_not_ready_idx.append(host_idx)
                else:
                    logging.info("Bats protocol is running on %s",
                                 all_hosts[host_idx].name())
            logging.info(
                f"############### checking round %d, not ready hosts: %s ###############",
                max_sleep_time, cur_not_ready_idx)
            not_ready_host_range = cur_not_ready_idx

        if len(not_ready_host_range) > 0:
            failed_hosts = ""
            for idx in not_ready_host_range:
                failed_hosts += f"{all_hosts[idx].name()} "
            logging.error(
                f"############### Oasis run bats protocol failed on "
                "%s ###############", failed_hosts)
            return False

        return True

    def stop(self, network: INetwork):
        all_hosts = network.get_hosts()
        if all_hosts is None:
            return False
        host_num = len(all_hosts)
        for i in range(host_num):
            logging.info(
                f"############### Oasis stop bats protocol on "
                "%s ###############",
                all_hosts[i].name())
            all_hosts[i].cmd(
                f'pkill -9 -f {self.process_name}')
            all_hosts[i].cmd(f'ip tuntap del mode tap tap')
            all_hosts[i].cmd(f'iptables -F -t nat')
        return True

    def _init_tun(self, host: IHost):
        host.cmd(f'mkdir /dev/net')
        host.cmd(f'mknod /dev/net/tun c 10 200')
        host.cmd(f'ip tuntap add mode tap tap')
        return True

    def _verify_license(self) -> bool:
        if not self.config.config_base_path:
            logging.error(
                "############### Config base path is not set ###############")
            return False
        self.license_path = f'{self.config.config_base_path}rootfs/etc/cfg/licence'
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

    def _init_config(self, host: IHost, id: int):
        # {host.name()} = h0, h1, h2, ... the last character is the index of the host
        host_idx = int(host.name()[-1])
        host.cmd(
            f'mkdir -p /etc/cfg')
        host.cmd(
            f'mkdir -p /etc/bats-protocol')
        if self.is_distributed_var:
            host.cmd(
                f'cp {self.log_config_dir}{id}/h{host_idx}.ini /etc/bats-protocol/bats-protocol-settings.ini')
            logging.info(
                f"############### Oasis install bats protocol config files on "
                "%s ###############",
                host.name())
        else:
            if self.proto_role == ProtoRole.client:
                host.cmd(
                    f'cp {self.log_config_dir}client/h0.ini /etc/bats-protocol/bats-protocol-settings.ini')
            elif self.proto_role == ProtoRole.server:
                host.cmd(
                    f'cp {self.log_config_dir}server/h1.ini /etc/bats-protocol/bats-protocol-settings.ini')
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

    def get_protocol_args(self, network: INetwork) -> str:
        return self.protocol_args
