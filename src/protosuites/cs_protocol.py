# import logging
from protosuites.proto import (ProtoConfig, IProtoSuite)
from interfaces.network import INetwork
from protosuites.proto_info import IProtoInfo

class CSProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, client:IProtoSuite, server:IProtoSuite):
        self.client = client
        self.server = server

    def post_run(self, network: INetwork):
        return self.client.post_run(network) and self.server.post_run(network)

    def pre_run(self, network: INetwork):
        if self.client.pre_run(network):
            return self.server.pre_run(network)
        return False
        # return self.client.pre_run(network) and self.server.pre_run(network)

    def run(self, network: INetwork, client_host:int, server_host:int):
        return self.client.run(network, client_host, server_host) \
                and self.server.run(network, client_host, server_host)

    def stop(self, network: INetwork):
        return self.client.stop(network) and self.server.stop

    def get_forward_port(self, network: 'INetwork', host_id: int) -> int:
        return self.client.get_forward_port(network, host_id)

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        return self.client.get_tun_ip(network, host_id)

    def get_protocol_name(self) -> str:
        return self.client.get_protocol_name()