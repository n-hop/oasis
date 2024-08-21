import logging
from protosuites.proto import (ProtoConfig, IProtoSuite)
from interfaces.network import INetwork
from .proto_info import IProtoInfo


class StdProtocol(IProtoSuite, IProtoInfo):
    """StdProtocol is used to load the protocol which be described in YAML.
    """

    def __init__(self, config: ProtoConfig):
        super().__init__(config)
        if self.config.path is not None:
            self.process_name = self.config.path.split('/')[-1]
        else:
            self.process_name = None
        self.forward_port = self.config.port

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork):
        if self.process_name is None:
            # means no need to run the protocol
            return True
        if self.config.type == 'none_distributed' and len(self.config.hosts) != 1:
            logging.error(
                "Test non-distributed protocols, but protocol server/client hosts are not set correctly.")
            return False
        hosts = network.get_hosts()
        for host in hosts:
            kcp_args = ''
            for arg in self.config.args:
                kcp_args += arg + ' '
            logging.info("host %s args: %s", host, kcp_args)
            if "%s" in kcp_args:
                receiver_ip = hosts[-1].IP()
                kcp_args = kcp_args % (receiver_ip, self.forward_port)
            host.cmdPrint(f'{self.config.path} {kcp_args} ')
            logging.info(
                f"############### Oasis start %s protocol on %s ###############", self.config.name, host.name())
        return True

    def stop(self, network: INetwork):
        if self.process_name is None:
            return True
        for host in network.get_hosts():
            host.cmdPrint(f'pkill -f {self.process_name}')
            logging.info(
                f"############### Oasis stop %s protocol on %s ###############", self.config.name, host.name())
        return True

    def get_forward_port(self) -> int:
        return self.forward_port

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass

    def get_protocol_name(self) -> str:
        return self.config.name.upper()

    def get_protocol_version(self) -> str:
        return self.config.version