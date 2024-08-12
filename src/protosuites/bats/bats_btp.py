from interfaces.network import INetwork
from protosuites.proto import IProtoSuite
from protosuites.proto_info import IProtoInfo


class BTP(IProtoSuite, IProtoInfo):
    """BATS protocol BTP-TUN mode
    """

    def __init__(self, bats_protocol: IProtoSuite):
        super().__init__(bats_protocol.config)
        self.bats_protocol = bats_protocol

    def post_run(self, network: INetwork):
        return self.bats_protocol.post_run(network)

    def pre_run(self, network: INetwork):
        return self.bats_protocol.pre_run(network)

    def run(self, network: INetwork):
        return self.bats_protocol.run(network)

    def stop(self, network: INetwork):
        return self.bats_protocol.stop(network)

    def get_forward_port(self, network: 'INetwork', host_id: int) -> int:
        pass

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass
