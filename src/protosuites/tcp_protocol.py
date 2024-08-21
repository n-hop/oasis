from interfaces.network import INetwork
from protosuites.proto import (IProtoSuite)
from .proto_info import IProtoInfo


class TCPProtocol(IProtoSuite, IProtoInfo):
    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork):
        return True

    def stop(self, network: INetwork):
        return True

    def get_forward_port(self) -> int:
        return None

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass

    def get_protocol_name(self) -> str:
        return "TCP"

    def get_protocol_version(self) -> str:
        return self.config.version
