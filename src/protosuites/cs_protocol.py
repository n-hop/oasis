import logging
from interfaces.network import INetwork
from protosuites.proto import (ProtoConfig, IProtoSuite)
from protosuites.proto_info import IProtoInfo


class CSProtocol(IProtoSuite, IProtoInfo):
    def __init__(self, config: ProtoConfig, client: IProtoSuite, server: IProtoSuite):
        super().__init__(config)
        self.client = client
        self.server = server

    def is_distributed(self) -> bool:
        return False

    def post_run(self, network: INetwork):
        return self.client.post_run(network) and self.server.post_run(network)

    def pre_run(self, network: INetwork):
        if self.client.pre_run(network):
            return self.server.pre_run(network)
        return False
        # return self.client.pre_run(network) and self.server.pre_run(network)

    def run(self, network: INetwork):
        if len(self.config.hosts) != 2:
            logging.error(
                "Test non-distributed protocols, but protocol server/client hosts are not set correctly.")
            return False
        self.client.get_config().hosts = [self.config.hosts[0]]
        self.server.get_config().hosts = [self.config.hosts[1]]
        # add self.config.args to client and server
        self.client.get_config().args += self.config.args
        self.server.get_config().args += self.config.args
        return self.client.run(network) \
            and self.server.run(network)

    def stop(self, network: INetwork):
        return self.client.stop(network) and self.server.stop

    def get_forward_port(self) -> int:
        return self.client.get_forward_port()

    def get_tun_ip(self, network: 'INetwork', host_id: int) -> str:
        return self.client.get_tun_ip(network, host_id)

    def get_protocol_name(self) -> str:
        return self.client.get_protocol_name()
