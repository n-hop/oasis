import logging
import time
import re
from protosuites.proto import (ProtoConfig, IProtoSuite, ProtoRole)
from interfaces.network import INetwork


class StdProtocol(IProtoSuite):
    """StdProtocol is used to load the protocol which be described by YAML.
    """

    def __init__(self, config: ProtoConfig, is_distributed: bool = True, role: ProtoRole = ProtoRole.both):
        super().__init__(config, is_distributed, role)
        self.forward_port = self.config.port
        self.default_version_dict = {}

    def is_distributed(self) -> bool:
        return self.is_distributed_var

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        self.__set_protocol_version(network, self.get_protocol_version())
        return True

    def run(self, network: INetwork):
        if self.process_name is None:
            # means no need to run the protocol
            logging.debug(
                "No process name found, skip the protocol %s run.", self.config.name)
            return True
        if self.config.type == 'none_distributed':
            if self.config.hosts is None or len(self.config.hosts) != 2:
                logging.error(
                    "Test non-distributed protocols, but protocol server/client hosts are not set correctly.")
                return False
        hosts = network.get_hosts()
        if hosts is None:
            return False
        if self.config.hosts is None:
            # if not defined, then run on all hosts
            self.config.hosts = [0, len(hosts) - 1]
        for host_id in self.config.hosts:
            cur_protocol_args = self.get_protocol_args(network)
            hosts[host_id].cmd(
                f'{self.config.bin} {cur_protocol_args} > '
                f'{self.log_dir}{self.config.name}_h{host_id}.log &')
        time.sleep(2)
        for host_id in self.config.hosts:
            res = hosts[host_id].cmd(f"ps aux | grep {self.process_name}")
            if res.find(self.process_name) == -1:
                logging.error(
                    "Failed to start the protocol %s on %s", self.config.name, hosts[host_id].name())
                return False
            logging.info(
                f"############### Oasis start %s protocol on %s ###############",
                self.config.name, hosts[host_id].name())
        return True

    def stop(self, network: INetwork):
        # restore the protocol version
        self.__restore_protocol_version(network)
        if self.process_name is None:
            # means no need to stop the protocol
            return True
        hosts = network.get_hosts()
        if hosts is None:
            return False
        for host in hosts:
            host.cmd(f'pkill -9 -f {self.process_name}')
            logging.info(
                f"############### Oasis stop %s protocol on %s ###############",
                self.config.name, host.name())
        return True

    def get_forward_port(self) -> int:
        if self.forward_port is not None:
            return self.forward_port
        return 0

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        routing_type_name = network.get_routing_strategy().routing_type()
        if routing_type_name == 'OLSRRouting':
            host = network.get_hosts()[host_id]
            pf = host.popen(f"ip addr show lo label lo:olsr")
            if pf is None:
                return ""
            ip = pf.stdout.read().decode('utf-8')
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip)
            if match:
                return match.group(1)
            return ""
        return ""

    def get_protocol_name(self) -> str:
        return self.config.name

    def get_protocol_version(self) -> str:
        return self.config.version or ""

    def get_protocol_args(self, network: INetwork) -> str:
        hosts = network.get_hosts()
        if "%s" in self.protocol_args:
            receiver_ip = self.get_tun_ip(network, len(hosts) - 1)
            if receiver_ip == "":
                receiver_ip = hosts[-1].IP()
            if 'kcp' in self.config.name:
                return self.protocol_args % receiver_ip
            if 'quic_' in self.config.name:
                return self.protocol_args % (receiver_ip, receiver_ip)
        return self.protocol_args

    def __set_protocol_version(self, network: INetwork, version: str):
        if 'tcp' in self.config.name:
            self.__handle_tcp_version_setup(network, version)
            return True
        return True

    def __restore_protocol_version(self, network: INetwork):
        if not self.default_version_dict:
            # no need to restore
            return True
        if 'tcp' in self.config.name:
            self.__handle_tcp_version_restore(network)
            return True
        return True

    def __handle_tcp_version_restore(self, network: INetwork):
        hosts = network.get_hosts()
        for host in hosts:
            default_ver = self.default_version_dict[host.name()]
            if default_ver is None:
                continue
            host.cmd(
                f'sysctl -w net.ipv4.tcp_congestion_control={default_ver}')
            host.cmd(f"sysctl -p")
            logging.info(
                "############### Oasis change the congestion control"
                " algorithm back to %s on %s ###############", default_ver, host.name())
        return True

    def __handle_tcp_version_setup(self, network: INetwork, version: str):
        if version not in ['cubic', 'bbr', 'reno']:
            logging.error(
                "TCP version %s is not supported, please check the configuration.", version)
            return
        hosts = network.get_hosts()
        for host in hosts:
            # read `tcp_congestion_control` before change
            pf = host.popen(
                f"sysctl net.ipv4.tcp_congestion_control")
            if pf is None:
                logging.error(
                    "Failed to get the tcp congestion control on %s", host.name())
                continue
            res = pf.stdout.read().decode('utf-8')
            default_version = res.split('=')[-1].strip()
            if default_version == version:
                continue
            self.default_version_dict[host.name()] = default_version
            logging.debug("tcp default version on %s is %s",
                          host.name(), default_version)
            host.cmd(
                f'sysctl -w net.ipv4.tcp_congestion_control={version}')
            host.cmd(f"sysctl -p")
            logging.info(
                "############### Oasis change the congestion control"
                " algorithm to %s on %s ###############", version, host.name())
