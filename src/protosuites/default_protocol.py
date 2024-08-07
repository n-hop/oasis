from interfaces.network import INetwork
from .proto import IProtoSuite


class DefaultProtocol(IProtoSuite):
    def post_run(self, network: INetwork):
        return True

    def pre_run(self, network: INetwork):
        return True

    def run(self, network: INetwork):
        return True

    def stop(self, network: INetwork):
        return True
