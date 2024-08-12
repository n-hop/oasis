# import logging
from interfaces.network import INetwork
from .proto import IProtoSuite


class KCPProtocol(IProtoSuite):
    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork):
        return True

    def stop(self, network: INetwork):
        return True

    def get_forward_port(self, network: 'INetwork', host_id: int) -> int:
        pass

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        pass
