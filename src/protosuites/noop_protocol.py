import logging
from abc import ABC, abstractmethod
from interfaces.network import INetwork
from protosuites.proto import (ProtoConfig, IProtoSuite, ProtoRole)


def is_next_protocol(proto_name: str) -> bool:
    """Check if the protocol is a bats next protocol."""
    if '-next' in proto_name or '-NEXT' in proto_name:
        return True
    return False


def is_no_op_protocol(proto_name: str) -> bool:
    if 'tcp' in proto_name or 'TCP' in proto_name:
        return True
    if 'udp' in proto_name or 'UDP' in proto_name:
        return True
    return is_next_protocol(proto_name)


class ProtocolConfigInf(ABC):
    """ProtocolConfigInf is the interface for protocol version configuration."""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.default_version_dict = {}

    def __str__(self):
        return f"{self.name} {self.version}"

    @abstractmethod
    def setup(self, network: 'INetwork') -> bool:  # type: ignore
        pass

    @abstractmethod
    def restore(self, network: 'INetwork') -> bool:  # type: ignore
        pass


class TCPConfigInf(ProtocolConfigInf):
    def setup(self, network: 'INetwork') -> bool:  # type: ignore
        if self.version not in ['cubic', 'bbr', 'reno']:
            logging.error(
                "TCP version %s is not supported, please check the configuration.", self.version)
            return False
        hosts = network.get_hosts()
        # read `tcp_congestion_control` before change
        for host in hosts:
            pf = host.popen(
                f"sysctl net.ipv4.tcp_congestion_control")
            if pf is None:
                logging.error(
                    "Failed to get the tcp congestion control on %s", host.name())
                continue
            res = pf.stdout.read().decode('utf-8')
            default_version = res.split('=')[-1].strip()
            if default_version == self.version:
                logging.info(
                    "tcp default version on %s is already %s, skip the setup.",
                    host.name(), default_version)
                continue
            self.default_version_dict[host.name()] = default_version
            logging.debug("tcp default version on %s is %s",
                          host.name(), default_version)
            host.cmd(
                f'sysctl -w net.ipv4.tcp_congestion_control={self.version}')
            host.cmd(f"sysctl -p")
            logging.info(
                "############### Oasis set the congestion control"
                " algorithm to %s on %s ###############", self.version, host.name())
        return True

    def restore(self, network: 'INetwork') -> bool:  # type: ignore
        # skip restore when the default_version_dict is empty
        if not self.default_version_dict:
            logging.info(
                "############### Oasis TCPConfigInf restore skipped ###############")
            return True
        hosts = network.get_hosts()
        for host in hosts:
            default_ver = None
            if host.name() in self.default_version_dict:
                default_ver = self.default_version_dict[host.name()]
            else:
                logging.warning(
                    f"Host %s not found in default_version_dict during restore.", host.name())
            if default_ver is None:
                continue
            host.cmd(
                f'sysctl -w net.ipv4.tcp_congestion_control={default_ver}')
            host.cmd(f"sysctl -p")
            logging.info(
                "############### Oasis restore the congestion control"
                " algorithm to %s on %s ###############", default_ver, host.name())
        return True


class NoOpProtocol(IProtoSuite):
    """NoOpProtocol are the protocols which are built-in in the system. No need to run any process.
    """

    def __init__(self, config: ProtoConfig, is_distributed: bool = True, role: ProtoRole = ProtoRole.both):
        super().__init__(config, is_distributed, role)
        self.forward_port = self.config.port
        self.proto_version_config_inf = None
        if 'tcp' in self.config.name.lower():
            self.proto_version_config_inf = TCPConfigInf(
                'tcp', self.config.version or 'cubic')
        logging.info("NoOpProtocol initialized for: %s", self.config.name)

    def is_distributed(self) -> bool:
        return self.is_distributed_var

    def is_noop(self) -> bool:
        return True

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        if self.proto_version_config_inf:
            self.proto_version_config_inf.setup(network)
        return True

    def run(self, network: INetwork):
        return True

    def stop(self, network: INetwork):
        if self.proto_version_config_inf:
            self.proto_version_config_inf.restore(network)
        return True

    def get_protocol_name(self) -> str:
        return self.config.name

    def get_protocol_version(self) -> str:
        return self.config.version or ""

    def get_protocol_args(self, network: INetwork) -> str:
        return self.protocol_args

    def get_forward_port(self) -> int:
        if self.forward_port is not None:
            return self.forward_port
        return 0

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        return ""
