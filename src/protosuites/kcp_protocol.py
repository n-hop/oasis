import logging
from protosuites.proto import (ProtoConfig, IProtoSuite)
from interfaces.network import INetwork
from .proto_info import IProtoInfo


class KCPProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config: ProtoConfig):
        super().__init__(config)
        if self.config.path is None:
            logging.error("No protocol path specified.")
        self.process_name = self.config.path.split('/')[-1]
        self.forward_port = 5201

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork):
        hosts = network.get_hosts()
        if len(self.config.hosts) != 1:
            logging.error(
                "Test non-distributed protocols, but protocol server/client hosts are not set correctly.")
            return False
        host_id = self.config.hosts[0]
        kcp_args = ''
        for arg in self.config.args:
            kcp_args += arg + ' '
        logging.info("host %s args: %s", host_id, kcp_args)
        if "%s" in kcp_args:
            receiver_ip = hosts[-1].IP()
            kcp_args = kcp_args % (receiver_ip, self.forward_port)
        hosts[host_id].cmdPrint(f'{self.config.path} {kcp_args} ')
        return True

    def stop(self, network: INetwork):
        host_id = self.config.hosts[0]
        hosts = network.get_hosts()
        hosts[host_id].cmdPrint(f'pkill -f {self.process_name}')
        logging.info(
            f"############### Oasis stop kcp protocol on %s ###############", hosts[host_id].name())
        return True

    def get_forward_port(self) -> int:
        return self.forward_port

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass

    def get_protocol_name(self) -> str:
        return "KCP"

    def get_protocol_version(self) -> str:
        return self.config.version
