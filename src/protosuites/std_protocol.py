import logging
import time
import re
from protosuites.proto import (ProtoConfig, IProtoSuite, ProtoRole)
from interfaces.network import INetwork


class StdProtocol(IProtoSuite):
    """StdProtocol is the protocol with the user process running on the host. It can accept arguments from YAML config.
    """

    def __init__(self, config: ProtoConfig, is_distributed: bool = True, role: ProtoRole = ProtoRole.both):
        super().__init__(config, is_distributed, role)
        self.forward_port = self.config.port
        if self.process_name is None:
            logging.warning(
                "No process name found for StdProtocol %s .", self.config.name)

    def is_distributed(self) -> bool:
        return self.is_distributed_var

    def is_noop(self) -> bool:
        return False

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork):
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
            if self.process_name and res.find(self.process_name) == -1:
                logging.error(
                    "Failed to start the protocol %s on %s", self.config.name, hosts[host_id].name())
                return False
            logging.info(
                f"############### Oasis start %s protocol on %s ###############",
                self.config.name, hosts[host_id].name())
        return True

    def stop(self, network: INetwork):
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
        return self.protocol_args
