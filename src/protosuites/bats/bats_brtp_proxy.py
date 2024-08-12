from interfaces.network import INetwork
from protosuites.proto import IProtoSuite
from protosuites.proto_info import IProtoInfo


class BRTPProxy(IProtoSuite, IProtoInfo):
    """BATS protocol BRTP-proxy mode.
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

    def get_forward_port(self) -> int:
        # The Iperf3 default port 5201 is set to exclude_port on the ini, for TCP proxy we use 5202
        return 5202

    def get_tun_ip(self) -> str:
        pass
