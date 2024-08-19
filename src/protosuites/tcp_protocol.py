from interfaces.network import INetwork
from protosuites.proto import (ProtoConfig, IProtoSuite)
from .proto_info import IProtoInfo

class TCPProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config: ProtoConfig):
        super().__init__(config)

    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork, client_host:int, server_host:int):
        return True

    def stop(self, network: INetwork):
        return True

    def get_forward_port(self, network: 'INetwork', host_id: int) -> int:
        pass

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass

    def get_protocol_name(self) -> str:
        return "tcp"
