import logging
from protosuites.proto import (ProtoConfig, IProtoSuite)
from interfaces.network import INetwork
from .proto_info import IProtoInfo


class StdProtocol(IProtoSuite, IProtoInfo):
    """StdProtocol is used to load the protocol which be described by YAML.
    """

    def __init__(self, config: ProtoConfig):
        super().__init__(config)
        if self.config.path is not None:
            self.process_name = self.config.path.split('/')[-1]
        else:
            self.process_name = None
        self.forward_port = self.config.port
        self.default_version_dict = {}

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        self.__set_protocol_version(network, self.get_protocol_version())
        return True

    def run(self, network: INetwork):
        if self.process_name is None:
            # means no need to run the protocol
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
            cur_protocol_args = self.get_protocol_args(hosts)
            hosts[host_id].cmd(f'{self.config.path} {cur_protocol_args} &')
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
            host.cmd(f'pkill -f {self.process_name}')
            logging.info(
                f"############### Oasis stop %s protocol on %s ###############",
                self.config.name, host.name())
        return True

    def get_forward_port(self) -> int:
        if self.forward_port is not None:
            return self.forward_port
        return 0

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        return ""

    def get_protocol_name(self) -> str:
        return self.config.name

    def get_protocol_version(self) -> str:
        return self.config.version or ""

    def get_protocol_args(self, hosts) -> str:
        if "%s" in self.protocol_args:
            receiver_ip = hosts[-1].IP()  # ?fixme
            if 'kcp' in self.config.name:
                return self.protocol_args % receiver_ip
            if 'quic_' in self.config.name:
                return self.protocol_args % (self.forward_port,
                                             receiver_ip,
                                             self.forward_port,
                                             receiver_ip
                                             )
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
        if hosts is None:
            return False
        for host in hosts:  # type: ignore
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
        if hosts is None:
            return
        for host in hosts:  # type: ignore
            # read `tcp_congestion_control` before change
            res = host.popen(
                f"sysctl net.ipv4.tcp_congestion_control").stdout.read().decode('utf-8')
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
